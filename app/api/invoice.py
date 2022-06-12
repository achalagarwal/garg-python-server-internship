
from collections import defaultdict
from datetime import datetime
import enum
from re import sub
from typing import Any, List, Tuple, Union
from urllib.error import HTTPError
import uuid
from fastapi import APIRouter, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse

from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.schemas import Invoice as InvoiceSchema, UserDB, InvoiceCreate, WarehouseInvoice as WarehouseInvoiceSchema
from app.models import SKU, Invoice, SKUVariant, WarehouseInventory, WarehouseInvoice, WarehouseInvoiceDetails
from app.schemas import invoice
from app.schemas.invoice import Status as InvoiceStatus, WarehouseInvoicePatch, WarehouseInvoiceResponse, WarehouseInvoiceDetails as WarehouseInvoiceDetailsSchema
from app.schemas.warehouse_inventory import WarehouseInventoryPick
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, over
from sqlalchemy.orm import joinedload

invoice_router = APIRouter()
client = AsyncClient(base_url="http://localhost:8000/")


@invoice_router.post("/invoice", response_model=InvoiceSchema)
async def post_invoice(
    force_create: bool,
    invoice_data: InvoiceCreate,
    session: AsyncSession = Depends(get_session),
):

    # TODO: Cache total quantity per SKU
    # Use that quantity during invoice creation to check if possible to create invoice
    # Then set invoice.status = PENDING_CREATION; return response
    # Add a background task to convert PENDING_CREATION to PENDING_WAREHOUSE

    invoice_dict = invoice_data.dict(skip_defaults=True)
    invoice_dict["id"] = uuid.uuid4()
    invoice_dict["status"] = InvoiceStatus.PENDING.value
    invoice = Invoice(**invoice_dict)

    session.add(invoice)

    await session.flush()
    if len(invoice.items) == 0:
        raise HTTPException(status_code=422, detail=[{"loc": ["Items"] , "msg": "missing"}])

    sku_variants_query = select(SKUVariant).where(SKUVariant.parent_sku_id.in_(invoice.items)).order_by(SKUVariant.created_at)
    # fetch all locations for FIFO sku variant
    # if necessary split an invoice row into two (for multiple locations)
    # for index, sku_id in enumerate(invoice.items):
        # fetch 
    # .scalar_subquery can be used
    # q1 = select(SKUVariant.parent_sku_id, func.array_agg(aggregate_order_by(SKUVariant.created_at))[1]).group_by(SKUVariant.parent_sku_id).order_by(SKUVariant.created_at).limit(1)
    sku_variants_result = await session.execute(sku_variants_query)
    sku_variants: List[SKUVariant] = sku_variants_result.scalars().all()

    sku_variant_to_parent_sku = {sku_variant.id: sku_variant.parent_sku_id for sku_variant in sku_variants}

    # TODO: Filter out expired variants
    sku_variants_map = defaultdict(lambda: [])

    for sku_variant in sku_variants:
        sku_variants_map[sku_variant.parent_sku_id].append(sku_variant)
 
    oldest_sku_variant_ids = set(sku_variants_list[0].id for _, sku_variants_list in sku_variants_map.items())

    # TODO: detect best warehouse_id depending on availability of items and destination address
    warehouse_inventories_query = select(WarehouseInventory).where(WarehouseInventory.sku_variants.op('&&')(oldest_sku_variant_ids))
    warehouse_inventories_result = await session.scalars(warehouse_inventories_query)
    warehouse_inventories: List[WarehouseInventory] = warehouse_inventories_result.all()

    # TODO: Might make sense to get all the possible warehouse inventories for all skus
    # Then find the best grouping for a particular invoice

    warehouse_inventory_picks: List[Tuple[uuid.UUID, WarehouseInventoryPick]] = []
    sku_quantity_remaining_map = {sku_id:invoice.quantities[i] for i, sku_id in enumerate(invoice.items)}

    for warehouse_inventory in warehouse_inventories:
        for index, sku_variant_id in enumerate(warehouse_inventory.sku_variants):
            if sku_variant_id not in oldest_sku_variant_ids:
                continue
            parent_sku_id = sku_variant_to_parent_sku[sku_variant_id]
            quantity_remaining = sku_quantity_remaining_map[parent_sku_id]
            if quantity_remaining > 0:
                quantity_in_inventory = warehouse_inventory.projected_quantities[index]
                take_from_inventory = min(quantity_remaining, quantity_in_inventory)
                new_projected_quantities = list(warehouse_inventory.projected_quantities)
                new_projected_quantities[index] -= take_from_inventory
                warehouse_inventory.projected_quantities = new_projected_quantities
                warehouse_inventory_picks.append(
                    (   
                        warehouse_inventory.id,
                        WarehouseInventoryPick(
                            row=warehouse_inventory.row,
                            column=warehouse_inventory.column,
                            sku_variant_id=sku_variant_id,
                            sku_id=parent_sku_id,
                            quantity=take_from_inventory
                        )
                    )
                )
                sku_quantity_remaining_map[parent_sku_id] -= take_from_inventory
    
        
    sku_quantity_remaining_map = dict(filter(lambda x: x[1] > 0, sku_quantity_remaining_map.items()))
    
    # we split / perform another query because the number of warehouse inventories can be very large for a given list of skus
    # TODO: start with the next two newer sku variants and then next 4
    next_sku_variant_ids = []
    for sublist in [sku_variants_map[sku_id][1:-1] for sku_id in sku_quantity_remaining_map]:
        next_sku_variant_ids.extend(sublist)
    
    # TODO: use best warehouse_id from above
    warehouse_inventories_query = select(WarehouseInventory).with_for_update().where(WarehouseInventory.sku_variants.op('&&')(next_sku_variant_ids))
    warehouse_inventories_result = await session.scalars(warehouse_inventories_query)
    warehouse_inventories: List[WarehouseInventory] = warehouse_inventories_result.all()

    # create a map from sku_variant_id to warehouse_inventories
    sku_variant_to_warehouse_inventories_and_index: List[Tuple[WarehouseInventory, int]] = defaultdict(list)
    for warehouse_inventory in warehouse_inventories:
        for index, sku_variant_id in enumerate(warehouse_inventory.sku_variants):
            sku_variant_to_warehouse_inventories_and_index[sku_variant_id].append((warehouse_inventory, index ))
    
    # TODO: For now we take the first warehouse inventory we get
    # Ideally we should aggregate, and find the best inventory for each variant given other items
    # Because the warehouse can be BIGGG

    for sku_id, quantity_remaining in sku_quantity_remaining_map.items():
        # 1:-1 because we have already consumed 0 above
        sku_variant_ids = sku_variants_map[sku_id][1:-1]
        for sku_variant_id in sku_variant_ids:
            if quantity_remaining == 0:
                break
            for warehouse_inventory, index in sku_variant_to_warehouse_inventories_and_index[sku_variant_id]:
                if quantity_remaining == 0:
                    break
                quantity_in_inventory = warehouse_inventory.project_quantities[index]
                take_from_inventory = min(quantity_remaining, quantity_in_inventory)
                new_projected_quantities = list(warehouse_inventory.projected_quantities)
                new_projected_quantities[index] -= take_from_inventory
                warehouse_inventory.projected_quantities = new_projected_quantities
                warehouse_inventory_picks.append(
                    (   
                        warehouse_inventory.id,
                        WarehouseInventoryPick(
                            row=warehouse_inventory.row,
                            column=warehouse_inventory.column,
                            sku_variant_id=sku_variant_id,
                            sku_id=sku_id,
                            quantity=take_from_inventory
                        )
                    )
                )
                quantity_remaining -= take_from_inventory
        sku_quantity_remaining_map[sku_id] = quantity_remaining

    sku_quantity_remaining_map = dict(filter(lambda x: x[1] > 0, sku_quantity_remaining_map.items()))

    if len(sku_quantity_remaining_map) > 0:
        if not force_create:
            await session.rollback()
            # TODO: return the items that caused the error
            # TODO: move this earlier in the flow
            raise HTTPException(status_code=422, detail=[{"loc": [str(sku_id)[0:6] + "..." + " Quantity: " + str(quantity) for sku_id, quantity in sku_quantity_remaining_map.items()] , "msg": "unavailable in warehouse"}] )

    # The sort should be S-shaped
    ## First sort rows
    ## Get row boundaries
    ## Sort within each boundary in alternate asc/desc fashion
    warehouse_inventory_picks.sort(key=lambda id_and_warehouse_inventory_pick: id_and_warehouse_inventory_pick[1].row)
    row_boundaries = []
    prev_row = None
    for i, (_, warehouse_inventory_item) in enumerate(warehouse_inventory_picks):
        if warehouse_inventory_item.row != prev_row:
            prev_row = warehouse_inventory_item.row
            row_boundaries.append(i)
        else:
            continue
    
    sorted_warehouse_inventory_picks: List[Tuple[uuid.UUID, WarehouseInventoryPick]] = []
    reversed = False
    for i, row_boundary in enumerate(row_boundaries):
        
        next_row_boundary = None
        if i+1 < len(row_boundaries):
            next_row_boundary = row_boundaries[i+1]
        
        sorted_warehouse_inventory_picks += sorted(
            warehouse_inventory_picks[row_boundary:next_row_boundary],
            key=lambda id_and_warehouse_inventory_pick: id_and_warehouse_inventory_pick[1].column,
            reverse=reversed
        )

        # reset sort to ascending if the next row is not adjacent to prev row
        if next_row_boundary is not None:
            if warehouse_inventory_picks[next_row_boundary][1].row != warehouse_inventory_picks[row_boundary][1].row + 1:
                reversed = False
            else:
                reversed = not reversed

    # Add the items that were not found in the inventory
    for sku_id, quantity in sku_quantity_remaining_map.items(): 
        sorted_warehouse_inventory_picks.append((None,
            WarehouseInventoryPick(
                row="-",
                column="-",
                sku_id=sku_id,
                sku_variant_id=None,
                quantity=quantity
            ))
        )

    # TODO: Create new Warehouse Invoice(s) row in db
    # TODO: Decide warehouse id instead of hardcoding
    warehouse_id = "e9d50f10-dd96-41ec-a2f0-73fa62042982"

    warehouse_invoice = WarehouseInvoice(
        id=uuid.uuid4(),
        parent_invoice_id=invoice.id,
        warehouse_id=warehouse_id,
        warehouse_inventories=list(
            map(
                lambda id_and_warehouse_inventory_pick:id_and_warehouse_inventory_pick[0],
                sorted_warehouse_inventory_picks
            )
        ),
        sku_variants=list(
            map(
                lambda id_and_warehouse_inventory_pick: id_and_warehouse_inventory_pick[1].sku_variant_id,
                sorted_warehouse_inventory_picks
            )
        ),
        skus=list(
            map(
                lambda id_and_warehouse_inventory_pick: id_and_warehouse_inventory_pick[1].sku_id,
                sorted_warehouse_inventory_picks
            )
        ),
        quantities=list(
            map(
                lambda id_and_warehouse_inventory_pick: id_and_warehouse_inventory_pick[1].quantity,
                sorted_warehouse_inventory_picks
            )
        ),
        created_at=datetime.utcnow()
    )

    session.add(warehouse_invoice)
    await session.commit()

    return invoice

@invoice_router.get("/invoice", response_model=List[InvoiceSchema], deprecated=True)
async def get_pending_invoices(page: int = 0, page_size:int = 25, session: AsyncSession = Depends(get_session)):
    invoices_result = await session.execute(select(Invoice).where(
            or_(Invoice.status == InvoiceStatus.PENDING, Invoice.status == InvoiceStatus.PICKING)
        ).order_by(Invoice.created_date).offset(page*page_size).limit(page_size)
    )
    invoices = invoices_result.scalars().all()
    invoices_result = []
    for invoice in invoices:
        invoice_result = invoice.__dict__
        invoice_items_result = await session.execute(select(SKU).where(
            SKU.id.in_([str(id) for id in invoice.items]),
        ))
        invoice_result["items"] = [invoice_items.__dict__ for invoice_items in invoice_items_result.scalars().all()]
        invoices_result.append(invoice_result)
    return invoices

@invoice_router.patch("/api/warehouse_invoice")
async def patch_invoice(
    id: str,
    warehouse_invoice_updates: WarehouseInvoicePatch,
    session: AsyncSession = Depends(get_session)
):
    warehouse_invoice = await session.execute(
        select(WarehouseInvoice).options(
            joinedload(WarehouseInvoice.parent_invoice).options(joinedload(Invoice.warehouse_invoices))
        ).where(WarehouseInvoice.id == id)
    )
    warehouse_invoice: WarehouseInvoice = warehouse_invoice.unique().scalar_one()

    warehouse_invoice.status = warehouse_invoice_updates.status
    for warehouse_invoice in warehouse_invoice.parent_invoice.warehouse_invoices:
        if warehouse_invoice.status != warehouse_invoice_updates.status:
            await session.commit()
            return
    
    warehouse_invoice.parent_invoice.status = warehouse_invoice_updates.status

    await session.commit()
    return

@invoice_router.get("/api/warehouse_invoice", response_model=WarehouseInvoiceResponse)
async def get_pending_invoices(warehouse_id: uuid.UUID, page: int = 0, page_size:int = 25, last_updated_timestamp:Union[str, None] = None, session: AsyncSession = Depends(get_session)):
    # warehouse_invoices_query = select(WarehouseInvoice).join(
    #         Invoice,
    #         Invoice.id == WarehouseInvoice.parent_invoice_id
    #     ).join(
    #         WarehouseInventory,
    #         WarehouseInventory.id.in_(
    #             [inventory_id for inventory_id in WarehouseInvoice.warehouse_inventories ]
    #             )   
    #         ).where(
    #             or_(Invoice.status == InvoiceStatus.PENDING, Invoice.status == InvoiceStatus.PICKING),
    #             WarehouseInvoice.warehouse_id == warehouse_id
    #         ).order_by(WarehouseInvoice.created_at).offset(page*page_size).limit(page_size)
    #  TODO: Debug the above query and combine both queries into one

    
    warehouse_invoices_query = select(WarehouseInvoice, Invoice).options(joinedload(WarehouseInvoice.parent_invoice)).join(
            Invoice,
            Invoice.id == WarehouseInvoice.parent_invoice_id
            ).where(
                or_(Invoice.status == InvoiceStatus.PENDING, Invoice.status == InvoiceStatus.PICKING, Invoice.status == InvoiceStatus.READY_FOR_TRANSIT),
                WarehouseInvoice.warehouse_id == warehouse_id,
                or_(WarehouseInvoice.status == InvoiceStatus.PENDING, WarehouseInvoice.status == InvoiceStatus.PICKING, WarehouseInvoice.status == InvoiceStatus.IN_TRANSIT, WarehouseInvoice.status == InvoiceStatus.READY_FOR_TRANSIT)
            ).order_by(WarehouseInvoice.created_at).offset(page*page_size).limit(page_size)

    if last_updated_timestamp:
        print(last_updated_timestamp)
        print(datetime.strptime(last_updated_timestamp))
        
        warehouse_invoices_query = warehouse_invoices_query.where(
            WarehouseInvoice.updated_at > datetime.strptime(last_updated_timestamp),
            Invoice.updated_at > datetime.strptime(last_updated_timestamp)
        )
    
    warehouse_invoices_result = await session.execute(warehouse_invoices_query)

    warehouse_invoices: List[WarehouseInvoice] = warehouse_invoices_result.scalars().all()
    

    # TODO: Fix, this will crash when there are no invoices
    response_updated_timestamp = warehouse_invoices[0].updated_at
    for warehouse_invoice in warehouse_invoices:
        response_updated_timestamp = max(response_updated_timestamp, warehouse_invoice.updated_at)
        response_updated_timestamp = max(response_updated_timestamp, warehouse_invoice.parent_invoice.updated_at)
 
    warehouse_invoices = list(filter(lambda x: x.status != InvoiceStatus.IN_TRANSIT, warehouse_invoices))

    warehouse_inventory_ids = []
    for warehouse_invoice in warehouse_invoices:
        warehouse_inventory_ids.extend(warehouse_invoice.warehouse_inventories)
    
    warehouse_inventories_result = await session.execute(
       select(WarehouseInventory.id, WarehouseInventory.row, WarehouseInventory.column).where(
            WarehouseInventory.id.in_(warehouse_inventory_ids),
        )
    )
    warehouse_inventories = warehouse_inventories_result.all()
    warehouse_inventories_map = { warehouse_inventory[0]:warehouse_inventory for warehouse_inventory in warehouse_inventories}

    warehouse_invoices_response = {"last_updated_at": response_updated_timestamp, "invoices": []}
    for warehouse_invoice in warehouse_invoices:
        warehouse_invoice_response = WarehouseInvoiceSchema(
            company=warehouse_invoice.parent_invoice.company,
            status=warehouse_invoice.status,
            id=warehouse_invoice.id,
            invoice_id=warehouse_invoice.parent_invoice.invoice_id,
            deliver_to=warehouse_invoice.parent_invoice.deliver_to,
            created_at=warehouse_invoice.created_at,
            warehouse_items=[
                WarehouseInventoryPick(
                    row=warehouse_inventories_map[warehouse_invoice.warehouse_inventories[i]].row,
                    column=warehouse_inventories_map[warehouse_invoice.warehouse_inventories[i]].column,
                    sku_id=warehouse_invoice.skus[i],
                    sku_variant_id=warehouse_invoice.sku_variants[i],
                    quantity=warehouse_invoice.quantities[i]
                ) for i in range(len(warehouse_invoice.skus)) if warehouse_invoice.warehouse_inventories[i]
            ] + [
                    WarehouseInventoryPick(
                            row="-",
                            column="-",
                            sku_id=warehouse_invoice.skus[i],
                            sku_variant_id=None,
                            quantity=warehouse_invoice.quantities[i]
                        ) for i in range(len(warehouse_invoice.skus)) if not warehouse_invoice.warehouse_inventories[i]
                ]
        )
        warehouse_invoices_response["invoices"].append(warehouse_invoice_response)

    return warehouse_invoices_response


@invoice_router.post("/api/warehouse_invoice_details")
async def post_warehouse_invoice_details(
    warehouse_invoice_details: WarehouseInvoiceDetailsSchema,
    session: AsyncSession = Depends(get_session)
):
    warehouse_invoice = await session.execute(
        select(WarehouseInvoice).where(
            WarehouseInvoice.id == warehouse_invoice_details.warehouse_invoice_id
        )
    )
    warehouse_invoice: WarehouseInvoice = warehouse_invoice.unique().scalar_one()
    warehouse_inventories = await session.execute(
        select(WarehouseInventory).where(
            WarehouseInventory.id.in_(
                warehouse_invoice.warehouse_inventories
            )
        )
    )

    warehouse_inventories: List[WarehouseInventory] = warehouse_inventories.scalars().all()

    warehouse_inventories_id_map = {wi.id: wi for wi in warehouse_inventories}


    initially_suggested_updates = []
    for i, warehouse_inventory_id in enumerate(warehouse_invoice.warehouse_inventories):
        if warehouse_inventory_id is None:
            continue
        warehouse_inventory = warehouse_inventories_id_map[warehouse_inventory_id]
        initially_suggested_updates.append({
            "row": warehouse_inventory.row,
            "column": warehouse_inventory.column,
            "sku_variant": warehouse_invoice.sku_variants[i],
            "quantity": warehouse_invoice.quantities[i]
        })
    
    initially_suggested_updates.sort(
        key=lambda update: (update["sku_variant"], update["row"], update["column"], update["quantity"])
    )

    actual_updates = list(map(
        lambda update: {
            "row": update.row,
            "column": update.column,
            "sku_variant": update.sku_variant_id,
            "quantity": update.quantity
        }, 
        warehouse_invoice_details.inventory_updates
        )
    )

    updates_are_matching = True

    if len(actual_updates) != len(initially_suggested_updates):
        updates_are_matching = False

    else:

        actual_updates.sort(
            key=lambda update: (update["sku_variant"], update["row"], update["column"], update["quantity"])
        )

        for i, suggested_update in enumerate(initially_suggested_updates):
            if suggested_update == actual_updates[i]:
                continue
            else:
                updates_are_matching = False
                break
            
    warehouse_invoice_details_object = WarehouseInvoiceDetails(
        id= uuid.uuid4(),
        warehouse_invoice_id = warehouse_invoice_details.warehouse_invoice_id,
        time_per_item = warehouse_invoice_details.time_per_item
    )

    if not updates_are_matching:
        warehouse_invoice_details_object.columns = list(map(lambda x: x["column"], actual_updates))
        warehouse_invoice_details_object.rows = list(map(lambda x: x["row"], actual_updates))
        warehouse_invoice_details_object.quantities = list(map(lambda x: x["quantity"], actual_updates))
        warehouse_invoice_details_object.sku_variants = list(map(lambda x: x["sku_variant"], actual_updates))

    session.add(warehouse_invoice_details_object)
    await session.commit()

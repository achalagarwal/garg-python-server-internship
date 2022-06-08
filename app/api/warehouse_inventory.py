
from collections import defaultdict
import datetime
from operator import and_
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse

from app.utils import index_with_default
from httpx import AsyncClient

from app.api.deps import get_session
from app.core import security
from app.schemas import WarehouseInventory as WarehouseInventorySchema, WarehouseInventoryCreate
from app.tests import utils
from app.models import SKU, SKUVariant, WarehouseInventory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from thefuzz import process

warehouse_inventory_router = APIRouter()

client = AsyncClient(base_url="http://localhost:8000/")

@warehouse_inventory_router.post("/warehouse_inventory", response_model=WarehouseInventorySchema)
async def post_warehouse_inventory(
    warehouse_inventory: WarehouseInventoryCreate,
    new_sku_variant: bool = False,
    session: AsyncSession = Depends(get_session)
):
    
    if new_sku_variant:
        # the body sku_variant should be None
        if warehouse_inventory.sku_variant_id is not None:
            print("Warehouse Inventory SKU Variant should be None if we are creating a new SKU Variant")
        new_sku_variant = SKUVariant(created_at=datetime.datetime.utcnow(), parent_sku_id=warehouse_inventory.sku_id, id=uuid4())
        session.add(new_sku_variant)
        await session.flush()
        warehouse_inventory.sku_variant_id = new_sku_variant.id


    # update / create warehouse inventory
    existing_warehouse_inventory_result = await session.execute(select(WarehouseInventory).where(
        and_(
            WarehouseInventory.row == warehouse_inventory.row,
            WarehouseInventory.column == warehouse_inventory.column,
            WarehouseInventory.warehouse_id == warehouse_inventory.warehouse_id
        )
    ))

    existing_warehouse_inventory: Optional[WarehouseInventory] = existing_warehouse_inventory_result.scalars().one_or_none()
    if existing_warehouse_inventory:
        sku_variant_index = index_with_default(existing_warehouse_inventory.sku_variants, warehouse_inventory.sku_variant_id)
        if sku_variant_index is not None:
            new_quantities = list(existing_warehouse_inventory.quantities)
            new_quantities[sku_variant_index] += warehouse_inventory.quantity

            
            if new_quantities[sku_variant_index] == 0:
                del new_quantities[sku_variant_index]

                # only update (delete entry) projected quantities 
                # when both quantities[i] and project_quantities[i] are 0
                new_sku_variants = list(existing_warehouse_inventory.sku_variants)
                new_projected_quantities = list(existing_warehouse_inventory.projected_quantities)
                del new_projected_quantities[sku_variant_index]
                del new_sku_variants[sku_variant_index]
                existing_warehouse_inventory.quantities = new_quantities
                existing_warehouse_inventory.sku_variants = new_sku_variants

            else:
                existing_warehouse_inventory.quantities = new_quantities
        else:
            new_quantities = list(existing_warehouse_inventory.quantities)
            new_quantities.append(warehouse_inventory.quantity)

            # As a Purchase Order is created before stock movement, this should rarely by needed
            # If it is, it means we need to update it to its correct value
            print("SKU Variant: ", warehouse_inventory.sku_variant_id, " has an incorrect projected quantity. Possibly unaccounted/missing from Purchase Orders")
            new_projected_quantities = list(existing_warehouse_inventory.projected_quantities)
            new_projected_quantities.append(0)
            new_sku_variants = list(existing_warehouse_inventory.sku_variants)
            new_sku_variants.append(warehouse_inventory.sku_variant_id)
            existing_warehouse_inventory.quantities = new_quantities
            existing_warehouse_inventory.sku_variants = new_sku_variants
            existing_warehouse_inventory.projected_quantities = new_projected_quantities
            
        session.add(existing_warehouse_inventory)
        await session.commit()

    else:
        
        # When moving items, this print will be triggered
        # We want to only check when a new sku variant id is created
        # or new items are added to an existing warehouse inventory
        print("Manually added new stock without a PI (Purchase Invoice)")

        warehouse_inventory = WarehouseInventory(
            id=uuid.uuid4(),
            row=warehouse_inventory.row,
            column=warehouse_inventory.column,
            warehouse_id=warehouse_inventory.warehouse_id,
            sku_variants=[warehouse_inventory.sku_variant_id],
            quantities=[warehouse_inventory.quantity],
            projected_quantities=[0]
        )
        session.add(warehouse_inventory)
        await session.commit()

    return None
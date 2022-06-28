import uuid
from datetime import datetime, timedelta
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    SKU,
    Invoice,
    SKUVariant,
    Warehouse,
    WarehouseInventory,
    WarehouseInvoice,
)
from app.schemas.invoice import Status as InvoiceStatus

pytestmark = pytest.mark.asyncio


async def test_get_warehouse_invoice_sends_pending_invoices(
    client: AsyncClient, session: AsyncSession
):

    warehouse = Warehouse(id=uuid.uuid4(), display_name="Warehouse")
    session.add(warehouse)

    new_invoice_ids = []
    pending_invoice__invoice_ids = set()

    for i in range(15):
        pending_invoice__invoice_id = f"test_invoice_{i}"
        new_invoice = Invoice(
            id=uuid.uuid4(),
            invoice_id=pending_invoice__invoice_id,
            items=[],
            quantities=[],
            company="TestCompany",
            status=InvoiceStatus.PENDING,
        )
        pending_invoice__invoice_ids.add(pending_invoice__invoice_id)
        new_invoice_ids.append(new_invoice.id)
        session.add(new_invoice)

    await session.flush()

    for invoice_id in new_invoice_ids:
        new_warehouse_invoice = WarehouseInvoice(
            id=uuid.uuid4(),
            parent_invoice_id=invoice_id,
            status=InvoiceStatus.PENDING,
            warehouse_inventories=[],
            sku_variants=[],
            skus=[],
            quantities=[],
            warehouse_id=warehouse.id,
        )
        session.add(new_warehouse_invoice)

    new_invoice_ids = []
    for _ in range(50):
        new_invoice = Invoice(
            id=uuid.uuid4(),
            invoice_id="test",
            items=[],
            quantities=[],
            company="TestCompany",
            status=InvoiceStatus.IN_TRANSIT,
        )
        new_invoice_ids.append(new_invoice.id)
        session.add(new_invoice)

    await session.flush()

    for invoice_id in new_invoice_ids:
        new_warehouse_invoice = WarehouseInvoice(
            id=uuid.uuid4(),
            parent_invoice_id=invoice_id,
            status=InvoiceStatus.IN_TRANSIT,
            warehouse_inventories=[],
            sku_variants=[],
            skus=[],
            quantities=[],
            warehouse_id=warehouse.id,
        )
        session.add(new_warehouse_invoice)

    await session.commit()

    warehouse_invoices_response = await client.get(
        f"/api/warehouse_invoice?warehouse_id={str(warehouse.id)}"
    )
    warehouse_invoices_payload = warehouse_invoices_response.json()
    warehouse_invoices = warehouse_invoices_payload["invoices"]

    received_warehouse_invoice__invoice_ids = {
        invoice["invoice_id"] for invoice in warehouse_invoices
    }

    assert pending_invoice__invoice_ids.issubset(
        received_warehouse_invoice__invoice_ids
    )


async def test_deleting_invoice_resets_warehouse_inventory(
    client: AsyncClient, session: AsyncSession
):
    async def create_sku_inventory(session: AsyncSession):
        warehouse = Warehouse(id=uuid.uuid4(), display_name="Warehouse")
        session.add(warehouse)

        sku1 = SKU(
            id=uuid.uuid4(),
            title="TestSKU1",
            quantity_unit="test",
            company="TestCompany",
        )
        sku2 = SKU(
            id=uuid.uuid4(),
            title="TestSKU2",
            quantity_unit="test",
            company="TestCompany",
        )
        sku3 = SKU(
            id=uuid.uuid4(),
            title="TestSKU3",
            quantity_unit="test",
            company="TestCompany",
        )
        session.add_all([sku1, sku2, sku3])
        await session.flush()
        sku_variant_1_1 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku1.id, created_at=datetime.utcnow()
        )
        sku_variant_1_2 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku1.id, created_at=datetime.utcnow()
        )
        sku_variant_2_1 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku2.id, created_at=datetime.utcnow()
        )
        sku_variant_2_2 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku2.id, created_at=datetime.utcnow()
        )
        sku_variant_3_1 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku3.id, created_at=datetime.utcnow()
        )
        sku_variant_3_2 = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku3.id, created_at=datetime.utcnow()
        )

        session.add_all(
            [
                sku_variant_1_1,
                sku_variant_1_2,
                sku_variant_2_1,
                sku_variant_2_2,
                sku_variant_3_1,
                sku_variant_3_2,
            ]
        )
        warehouse_inventory_1 = WarehouseInventory(
            id=uuid.uuid4(),
            row=1,
            column=1,
            warehouse_id=warehouse.id,
            sku_variants=[
                sku_variant_1_1.id,
                sku_variant_1_2.id,
                sku_variant_2_1.id,
                sku_variant_2_2.id,
                sku_variant_3_1.id,
                sku_variant_3_2.id,
            ],
            quantities=[100, 100, 100, 100, 100, 100],
            projected_quantities=[0, 10, 50, 100, 100, 200],
        )

        warehouse_inventory_2 = WarehouseInventory(
            id=uuid.uuid4(),
            row=2,
            column=2,
            warehouse_id=warehouse.id,
            sku_variants=[
                sku_variant_1_1.id,
                sku_variant_1_2.id,
                sku_variant_2_1.id,
                sku_variant_2_2.id,
                sku_variant_3_1.id,
                sku_variant_3_2.id,
            ],
            quantities=[100, 100, 100, 100, 100, 100],
            projected_quantities=[200, 100, 100, 50, 10, 0],
        )

        session.add_all([warehouse_inventory_1, warehouse_inventory_2])
        await session.commit()

    await create_sku_inventory(session=session)

    warehouse_inventories_result = await session.execute(select(WarehouseInventory))
    warehouse_inventories_after_deleting_force_created_invoice: List[
        WarehouseInventory
    ] = warehouse_inventories_result.scalars().all()
    initial_projected_quantities = [
        warehouse_inventory.projected_quantities
        for warehouse_inventory in warehouse_inventories_after_deleting_force_created_invoice
    ]

    skus_result = await session.execute(select(SKU))
    skus = skus_result.scalars().all()

    invoice_items = [str(sku.id) for sku in skus]
    invoice_quantities = [50 for _ in range(len(invoice_items))]

    create_invoice_response = await client.post(
        f"/invoice?force_create={False}",
        json={
            "company": "TestCompany",
            "items": invoice_items,
            "quantities": invoice_quantities,
            "invoice_id": "TestInvoice1",
        },
    )
    assert create_invoice_response.status_code == 200

    create_invoice_response = await client.post(
        f"/invoice?force_create={False}",
        json={
            "company": "TestCompany",
            "items": invoice_items,
            "quantities": invoice_quantities,
            "invoice_id": "TestInvoice2",
        },
    )
    assert create_invoice_response.status_code == 200

    delete_invoice_response = await client.delete(
        f"/invoice?force_delete={False}&invoice_id={create_invoice_response.json()['id']}"
    )
    assert delete_invoice_response.status_code == 200

    await session.commit()

    warehouse_inventories_result = await session.execute(select(WarehouseInventory))
    warehouse_inventories_after_deleting_one_invoice: List[
        WarehouseInventory
    ] = warehouse_inventories_result.scalars().all()
    projected_quantities_after_deleting_one_invoice = [
        warehouse_inventory.projected_quantities
        for warehouse_inventory in warehouse_inventories_after_deleting_one_invoice
    ]

    invoice_items = [str(sku.id) for sku in skus]
    invoice_quantities = [100 if i % 2 == 0 else 200 for i in range(len(invoice_items))]

    create_invoice_response = await client.post(
        f"/invoice?force_create={True}",
        json={
            "company": "TestCompany",
            "items": invoice_items,
            "quantities": invoice_quantities,
            "invoice_id": "TestInvoice2",
        },
    )
    assert create_invoice_response.status_code == 200

    await session.commit()

    delete_invoice_response = await client.delete(
        f"/invoice?force_delete={False}&invoice_id={create_invoice_response.json()['id']}"
    )
    assert delete_invoice_response.status_code == 200

    await session.commit()

    warehouse_inventories_result = await session.execute(select(WarehouseInventory))
    warehouse_inventories_after_deleting_force_created_invoice: List[
        WarehouseInventory
    ] = warehouse_inventories_result.scalars().all()
    projected_quantities_after_deleting_force_created_invoice = [
        warehouse_inventory.projected_quantities
        for warehouse_inventory in warehouse_inventories_after_deleting_force_created_invoice
    ]

    # Assert changes reverted after deleting a force_created invoice
    assert (
        projected_quantities_after_deleting_force_created_invoice
        == projected_quantities_after_deleting_one_invoice
    )

    current_invoices_result = await session.execute(
        select(Invoice).where(Invoice.status != InvoiceStatus.CANCELLED)
    )
    current_invoices = current_invoices_result.scalars().all()

    for invoice in current_invoices:
        delete_invoice_response = await client.delete(
            f"/invoice?force_delete={False}&invoice_id={invoice.id}"
        )
        assert delete_invoice_response.status_code == 200

    await session.commit()

    warehouse_inventories_result = await session.execute(select(WarehouseInventory))
    warehouse_inventories_after_deleting_force_created_invoice: List[
        WarehouseInventory
    ] = warehouse_inventories_result.scalars().all()
    projected_quantities_after_deleting_all_invoices = [
        warehouse_inventory.projected_quantities
        for warehouse_inventory in warehouse_inventories_after_deleting_force_created_invoice
    ]

    # `sorted` to make sure that the equality check is agnostic of the initial order
    assert sorted(projected_quantities_after_deleting_all_invoices) == sorted(
        initial_projected_quantities
    )


async def test_create_invoice_picks_oldest_sku_variants(
    client: AsyncClient, session: AsyncSession
):
    async def create_sku_inventory(session: AsyncSession):
        warehouse = Warehouse(id=uuid.uuid4(), display_name="Warehouse")
        session.add(warehouse)

        sku = SKU(
            id=uuid.uuid4(),
            title="TestSKU1",
            quantity_unit="test",
            company="TestCompany",
        )

        session.add(sku)
        await session.flush()

        sku_variant_newest = SKUVariant(
            id=uuid.uuid4(), parent_sku_id=sku.id, created_at=datetime.utcnow()
        )
        sku_variant_oldest = SKUVariant(
            id=uuid.uuid4(),
            parent_sku_id=sku.id,
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        sku_variant_old = SKUVariant(
            id=uuid.uuid4(),
            parent_sku_id=sku.id,
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        sku_variant_new = SKUVariant(
            id=uuid.uuid4(),
            parent_sku_id=sku.id,
            created_at=datetime.utcnow() - timedelta(days=1),
        )

        session.add_all(
            [sku_variant_newest, sku_variant_oldest, sku_variant_old, sku_variant_new]
        )

        warehouse_inventory_1 = WarehouseInventory(
            id=uuid.uuid4(),
            row=1,
            column=1,
            warehouse_id=warehouse.id,
            sku_variants=[
                sku_variant_newest.id,
                sku_variant_oldest.id,
                sku_variant_old.id,
                sku_variant_new.id,
            ],
            quantities=[100, 100, 100, 100],
            projected_quantities=[100, 100, 100, 100],
        )

        warehouse_inventory_2 = WarehouseInventory(
            id=uuid.uuid4(),
            row=2,
            column=2,
            warehouse_id=warehouse.id,
            sku_variants=[
                sku_variant_newest.id,
                sku_variant_oldest.id,
                sku_variant_old.id,
                sku_variant_new.id,
            ],
            quantities=[100, 100, 100, 100],
            projected_quantities=[100, 100, 100, 100],
        )

        session.add_all([warehouse_inventory_1, warehouse_inventory_2])
        await session.commit()

    await create_sku_inventory(session=session)

    sku_variants_result = await session.execute(select(SKUVariant))
    sku_variants = sku_variants_result.scalars().all()

    sku_variants_sorted = sorted(sku_variants, key=lambda x: x.created_at)

    skus_result = await session.execute(select(SKU))
    skus = skus_result.scalars().all()

    assert len(skus) == 1

    invoice_items = [str(skus[0].id)]
    invoice_quantities = [250]

    create_invoice_response = await client.post(
        f"/invoice?force_create={False}",
        json={
            "company": "TestCompany",
            "items": invoice_items,
            "quantities": invoice_quantities,
            "invoice_id": "TestInvoice1",
        },
    )
    assert create_invoice_response.status_code == 200

    await session.commit()

    warehouse_invoices_result = await session.execute(select(WarehouseInvoice))
    warehouse_invoices = warehouse_invoices_result.scalars().all()

    assert len(warehouse_invoices) == 1
    warehouse_invoice: WarehouseInvoice = warehouse_invoices[0]

    for i, sku_variant_id in enumerate(warehouse_invoice.sku_variants):
        if sku_variant_id == sku_variants_sorted[1].id:
            assert warehouse_invoice.quantities[i] == 50
        elif sku_variant_id == sku_variants_sorted[0].id:
            assert warehouse_invoice.quantities[i] == 100
        else:
            raise ValueError("We shouldn't get any other sku variant in this invoice")

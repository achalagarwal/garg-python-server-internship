
from collections import defaultdict
from operator import and_
from typing import Any, Dict, List, Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse

from app.utils import index_with_default
from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
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
async def post_sku_variant(
    warehouse_inventory: WarehouseInventoryCreate,
    session: AsyncSession = Depends(get_session)
):
    print(warehouse_inventory)
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
                new_sku_variants = list(existing_warehouse_inventory.sku_variants)
                del new_sku_variants[sku_variant_index]
                existing_warehouse_inventory.quantities = new_quantities
                existing_warehouse_inventory.sku_variants = new_sku_variants
            else:
                existing_warehouse_inventory.quantities = new_quantities
        else:
            new_quantities = list(existing_warehouse_inventory.quantities)
            new_quantities.append(warehouse_inventory.quantity)
            new_sku_variants = list(existing_warehouse_inventory.sku_variants)
            new_sku_variants.append(warehouse_inventory.sku_variant_id)
            existing_warehouse_inventory.quantities = new_quantities
            existing_warehouse_inventory.sku_variants = new_sku_variants
            
        session.add(existing_warehouse_inventory)
        await session.commit()

    else:
        warehouse_inventory_dict = warehouse_inventory.dict(skip_defaults=True)
        warehouse_inventory_dict.pop("sku_variant_id")
        warehouse_inventory_dict.pop("quantity")
        
        warehouse_inventory_dict["id"] = uuid.uuid4()
        warehouse_inventory_dict["sku_variants"] = [warehouse_inventory.sku_variant_id]
        warehouse_inventory_dict["quantities"] = [warehouse_inventory.quantity]
        warehouse_inventory = WarehouseInventory(**warehouse_inventory_dict)
        session.add(warehouse_inventory)
        await session.commit()

    return None
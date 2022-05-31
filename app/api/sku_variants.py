
from collections import defaultdict
from typing import Any, Dict, List
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse


from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import SKUVariant as SKUVariantSchema, SKUVariantCreate
from app.tests import utils
from app.models import SKU, SKUVariant, WarehouseInventory 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from thefuzz import process

sku_variant_router = APIRouter()

client = AsyncClient(base_url="http://localhost:8000/")


@sku_variant_router.get("/sku_variant", response_model=Dict)
async def get_sku_variant(sku_id: str, warehouse_id: UUID, session: AsyncSession = Depends(get_session)):

    sku_variants_result = await session.execute(select(SKUVariant).where(SKUVariant.parent_sku_id == sku_id))
    sku_variants = sku_variants_result.scalars().all()

    base_query = select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse_id) 
    query = base_query.where(WarehouseInventory.sku_variants.op('&&')([sku_variant.id for sku_variant in sku_variants]))
    
    inventory_result = await session.execute(query)
    inventory = inventory_result.scalars().all()

    sku_variants_result_dict = {sku_variant.id:{ "locations": [], "index": i } for i,sku_variant in enumerate(sorted(sku_variants, key=lambda x: x.created_at))}
    
    # inventory.location.sku_variants is likely to be a small sized array
    # so we loop on it and map on sku_variants
    for location in inventory:
        for i, location_sku_variant_id in enumerate(location.sku_variants):
            if location_sku_variant_id in sku_variants_result_dict:
                sku_variants_result_dict[location_sku_variant_id]["locations"].append({
                    "row": location.row,
                    "column": location.column,
                    "quantity": location.quantities[i],
                })

    print(sku_variants_result_dict)
    return sku_variants_result_dict

@sku_variant_router.post("/sku_variant", response_model=SKUVariantSchema)
async def post_sku_variant(
    sku_variant: SKUVariantCreate,
    session: AsyncSession = Depends(get_session)
):
    raise NotImplemented
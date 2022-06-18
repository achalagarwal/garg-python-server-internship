
from collections import defaultdict
from typing import Any, Dict, List
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse


from httpx import AsyncClient

from app.api.deps import get_session
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

@sku_variant_router.get("/api/sku_variant", response_model=Dict)
async def get_sku_variants(sku_id: str, warehouse_id: UUID, session: AsyncSession = Depends(get_session)):

    sku_variants_result = await session.execute(select(SKUVariant).where(SKUVariant.parent_sku_id == sku_id))
    sku_variants = sku_variants_result.scalars().all()
    
    # early return

    if len(sku_variants) == 0:
        return {}
    
    base_query = select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse_id) 
    query = base_query.where(WarehouseInventory.sku_variants.op('&&')([sku_variant.id for sku_variant in sku_variants]))
    
    inventory_result = await session.execute(query)
    inventory: List[WarehouseInventory] = inventory_result.scalars().all()
    sorted_sku_variants = sorted(sku_variants, key=lambda x: x.created_at)
    sorted_sku_variants_index_map = {sku_variant.id: i for i, sku_variant in enumerate(sorted_sku_variants)}

    sku_variants_result : Dict = {
        "default_add_sku_variant_id": sorted_sku_variants[-1].id,
        "sku_variants": [
                {"sku_variant": sku_variant, "locations": [] } for sku_variant in sorted_sku_variants
            ]
        }
    
    # inventory.location.sku_variants is likely to be a small sized array
    # so we loop on it and map on sku_variants
    for location in inventory:
        for i, location_sku_variant_id in enumerate(location.sku_variants):
            # this condition must be true, else it means we have incorrectly deleted an sku variant when it exists in the inventory
            # or the inventory quantity set is 0, which signifies corrupt data
            if (index_of_sku_variant_id := (sorted_sku_variants_index_map.get(location_sku_variant_id))) is not None:
                sku_variants_result["sku_variants"][index_of_sku_variant_id]["locations"].append({
                    "row": location.row,
                    "column": location.column,
                    "quantity": location.quantities[i],
                })

    
    # remove the sku variants that are not there in the inventory
    # and sort the locations by ROW and COL
    cleaned_sku_variants_result = {
        "default_add_sku_variant_id": sorted_sku_variants[-1].id,
        "sku_variants": []
    }
    for sku_variant_dict in sku_variants_result["sku_variants"]:
        sku_variant = sku_variant_dict["sku_variant"]
        locations = sku_variant_dict["locations"]
        if len(locations) == 0:
            continue
        else:
            cleaned_sku_variants_result["sku_variants"].append({
                "sku_variant": sku_variant,
                "locations": sorted(locations, key=lambda x: (x["row"], x["column"]))
            })


    return cleaned_sku_variants_result

@sku_variant_router.get("/sku_variant", response_model=Dict)
async def get_sku_variants(sku_id: str, warehouse_id: UUID, session: AsyncSession = Depends(get_session)):

    sku_variants_result = await session.execute(select(SKUVariant).where(SKUVariant.parent_sku_id == sku_id))
    sku_variants = sku_variants_result.scalars().all()

    base_query = select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse_id) 
    query = base_query.where(WarehouseInventory.sku_variants.op('&&')([sku_variant.id for sku_variant in sku_variants]))
    
    inventory_result = await session.execute(query)
    inventory: List[WarehouseInventory] = inventory_result.scalars().all()

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

    # remove the sku variants that are not there in the inventory
    # for sku_variant_id, location_data in list(sku_variants_result_dict.items()):
    #     if len(location_data["locations"]) == 0:
    #         del sku_variants_result_dict[sku_variant_id]

    return sku_variants_result_dict

@sku_variant_router.post("/sku_variant", response_model=SKUVariantSchema)
async def post_sku_variant(
    sku_variant: SKUVariantCreate,
    session: AsyncSession = Depends(get_session)
):
    raise NotImplemented
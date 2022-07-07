from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient
from pydantic import UUID4
from sqlalchemy import distinct, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only

from app.api.deps import get_session
from app.models import SKU, SKUVariant
from app.schemas.sku import SKUMerge

sku_management_router = APIRouter()
client = AsyncClient(base_url="http://localhost:8000/")


@sku_management_router.post(
    "/api/sku_management/merge_skus", response_model=Literal[None]
)
async def merge_skus(
    sku_merged_data: SKUMerge,
    session: AsyncSession = Depends(get_session),
):

    sku_ids: List[UUID4] = sku_merged_data.sku_ids
    primary_sku_id: List[UUID4] = sku_merged_data.primary_sku_id

    all_sku_ids = sku_ids
    all_sku_ids.append(primary_sku_id)
    all_sku_ids = list(set(all_sku_ids))

    skus = await session.execute(
        select(SKU)
        .options(
            load_only(
                SKU.company,
                SKU.id,
                SKU.image_id,
                SKU.quantity_unit,
                SKU.title,
                SKU.price_unit,
                SKU.active_parent_sku_id,
                SKU.disabled,
                SKU.description,
            ),
            joinedload(SKU.sku_variants).options(load_only(SKUVariant.id)),
        )
        .where(SKU.id.in_(all_sku_ids))
    )

    sku_objects: List[SKU] = skus.unique().scalars().all()

    sku_id_map = {sku.id: sku for sku in sku_objects}

    active_parent_skus_result = await session.execute(
        select(distinct(SKU.active_parent_sku_id)).where(
            SKU.active_parent_sku_id.in_(all_sku_ids)
        )
    )

    active_parent_sku_list: List[SKU] = active_parent_skus_result.scalars().all()

    if len(active_parent_sku_list) > 1:
        print("Multiple active parent SKU provided, cannot merge")
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["parent_sku_id"], "msg": "multiple parents found"}],
        )
        return

    # otherwise if this list is empty then user must have provided primary sku
    # which is taken as param in primary_sku_id (line 53)

    if len(active_parent_sku_list) == 1 and active_parent_sku_list[0] != primary_sku_id:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["parent_sku_id"], "msg": "multiple parents found"}],
        )

    elif len(active_parent_sku_list) == 1:
        primary_sku_id = active_parent_sku_list[0]

    # so at this point we have the primary_sku_id, now we need to filter out
    # secondary SKU's and disable them

    secondary_skus = list(
        map(
            lambda id: sku_id_map[id],
            filter(lambda id: id != primary_sku_id, sku_id_map.keys()),
        )
    )

    primary_sku = sku_id_map[primary_sku_id]

    if primary_sku.disabled == True:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["parent_sku_id"], "msg": "primary SKU is disabled"}],
        )

    try:
        companies = set(
            map(
                lambda sku: sku.company,
                filter(lambda sku: sku.company is not None, sku_objects),
            )
        )
        assert len(companies) < 2
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["parent_sku_id"],
                    "msg": "SKU company should be same and exist",
                }
            ],
        )

    try:
        price_units = set(
            map(
                lambda sku: sku.price_unit,
                filter(lambda sku: sku.price_unit is not None, sku_objects),
            )
        )
        assert len(price_units) < 2
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["parent_sku_id"],
                    "msg": "SKU price unit should be same and exist",
                }
            ],
        )

    try:
        quantity_units = set(
            map(
                lambda sku: sku.quantity_unit,
                filter(lambda sku: sku.quantity_unit is not None, sku_objects),
            )
        )
        assert len(quantity_units) < 2
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["parent_sku_id"],
                    "msg": "SKU quantity unit should be same and exist",
                }
            ],
        )

    joined_description = "\n".join(
        filter(lambda x: x is not None, map(lambda x: x.title, secondary_skus))
    )
    if primary_sku.description:
        primary_sku.description += "\n" + joined_description
    else:
        primary_sku.description = "\n" + joined_description

    if not primary_sku.image_id:
        primary_sku.image_id = next(
            filter(lambda sku: sku.image_id is not None, secondary_skus), primary_sku
        ).image_id

    for sku in secondary_skus:
        sku.disabled = True

    all_sku_variants: List[UUID4] = []
    for sku in sku_objects:
        all_sku_variants.extend(sku.sku_variants)

    await session.flush()
    await session.execute(
        update(SKUVariant)
        .where(SKUVariant.id.in_([sku_variant.id for sku_variant in all_sku_variants]))
        .values(parent_sku_id=primary_sku_id)
    )

    await session.execute(
        update(SKU)
        .where(SKU.id.in_([sku.id for sku in sku_objects]))
        .values(active_parent_sku_id=primary_sku_id)
    )
    await session.commit()
    return

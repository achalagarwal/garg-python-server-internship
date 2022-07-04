from http.client import HTTPException
from typing import List, Literal

from fastapi import APIRouter, Depends
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


@sku_management_router.post("/merge", response_model=Literal[None])
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
                SKU.quantity_unit,
                SKU.title,
                SKU.price_unit,
                SKU.active_parent_sku_id,
                SKU.disabled,
            ),
            joinedload(SKU.sku_variants).options(load_only(SKUVariant.id)),
        )
        .where(SKU.id.in_(all_sku_ids))
    )

    # make a list of skus we fetched
    sku_objects: List[SKU] = skus.unique().scalars().all()
    # dict of sku_id : sku
    sku_id_map = {sku.id: sku for sku in sku_objects}

    # returns the parent id of sku, distinct keyword returns only 1 parent for multiple skus with same parent
    active_parent_skus_result = await session.execute(
        select(distinct(SKU.active_parent_sku_id)).where(
            SKU.active_parent_sku_id.in_(all_sku_ids)
        )  # check for not null
    )

    active_parent_sku_list: List[SKU] = active_parent_skus_result.scalars().all()

    # above list must ideally return 1 active parent id, that id is taken as the primary sku id

    if len(active_parent_sku_list) >= 2:
        print("Multiple active parent SKU provided, cannot merge")
        raise HTTPException(
            status_code=442,
            detail=[{"loc": ["parent_sku_id"], "msg": "multiple parents found"}],
        )
        return

    elif len(active_parent_sku_list) == 1:
        primary_sku_id = active_parent_sku_list[0]

    # otherwise if this list is empty then user must have provided primary sku
    # which is taken as param in primary_sku_id (line 53)

    if active_parent_sku_list[0] != primary_sku_id:
        raise HTTPException(
            status_code=442,
            detail=[{"loc": ["parent_sku_id"], "msg": "multiple parents found"}],
        )

    # """
    # so at this point we have the primary_sku_id, now we need to filter out
    # secondary SKU's and disable them
    # finally we will update the SKUs and SKU Variants
    # """
    # get secondary skus
    secondary_sku_id_list = []
    secondary_skus: List[SKU] = []
    for sku_id, sku in sku_id_map.items():
        if sku_id != primary_sku_id:
            secondary_sku_id_list.append(sku_id)
            secondary_skus.append(sku_id_map[sku_id])
        else:
            continue

    # disable secondary skus
    for sku in secondary_skus:
        sku.disabled = True

    all_sku_variants: List[UUID4] = []
    for sku in sku_objects:
        all_sku_variants.extend(sku.sku_variants)

    await session.flush()
    await session.execute(
        update(SKUVariant)
        .where(SKUVariant.id.in_(all_sku_variants))
        .values(parent_sku_id=primary_sku_id)
    )

    await session.execute(
        update(SKU)
        .where(SKU.id.in_(sku_objects))
        .values(active_parent_sku_id=primary_sku_id)
    )
    await session.commit()
    return

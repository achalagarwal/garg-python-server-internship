from uuid import UUID
from typing import List
from sqlalchemy import select, update, or_
from sqlalchemy.orm import joinedload, load_only
from app.models import SKU, SKUVariant, WarehouseInventory
from app.session import async_session
from thefuzz.fuzz import WRatio

import asyncio
import sys
async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: sys.stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)
# TODO: Add parameter to filter out SKUs to scan
async def recommend_merge_skus(company: str, threshold=90):

    # all_skus = await session.execute(
    #     select(SKU).options(
    #         load_only(SKU.id, SKU.title)
    #     ).where(or_(SKU.company == company, SKU.company == None))
    # )
    session = async_session()
    all_skus = await session.execute(
        select(SKU).where(or_(SKU.company == company, SKU.company == None))
    )
    all_skus = all_skus.scalars().all()
    sku_id_map = {sku.id: sku for sku in all_skus}
    groups = {i:{sku.id} for i,sku in enumerate(all_skus)} # dict with number keys
    sku_id_to_group_map = {sku.id:i for i, sku in enumerate(all_skus)} # sku id to groups key
    # disjoint group for each sku_id
    dissimilar_for_sku_map = {}

    # group_id_to_sku_set_map = {}

    for i, sku in enumerate(all_skus):
        for inner_sku in all_skus[i+1:]:
            if sku_id_to_group_map[inner_sku.id] == sku_id_to_group_map[sku.id]:
                continue
            # if transient disimilar
            # i.e. if one is similar to someone which is disimilar to another
            # add to dissimilar and continue
            similar_to_sku = groups[sku_id_to_group_map[sku.id]]

            dissimilar_to_inner_sku = dissimilar_for_sku_map.get(inner_sku.id, set())
            if len(similar_to_sku & dissimilar_to_inner_sku) > 0:
                dissimilar_to_inner_sku.add(sku.id)
                dissimilar_to_sku = dissimilar_for_sku_map.get(sku.id, set())
                dissimilar_to_sku.add(inner_sku.id)
                dissimilar_for_sku_map[inner_sku.id] = dissimilar_to_inner_sku
                dissimilar_for_sku_map[sku.id] = dissimilar_to_sku

                continue

            if (score:= WRatio(sku.title, inner_sku.title)) > threshold:
                print(score)
                groups[sku_id_to_group_map[sku.id]] |= groups[sku_id_to_group_map[inner_sku.id]]
                prev_group = sku_id_to_group_map[inner_sku.id]
                for id in groups[sku_id_to_group_map[inner_sku.id]]:
                     sku_id_to_group_map[id] = sku_id_to_group_map[sku.id]
                del groups[prev_group]
                # sku_id_to_group_map[inner_sku.id] = sku_id_to_group_map[sku.id]
            else:
                dissimilar_to_inner_sku = dissimilar_for_sku_map.get(inner_sku.id, set())
                dissimilar_to_inner_sku.add(sku.id)
                dissimilar_to_sku = dissimilar_for_sku_map.get(sku.id, set())
                dissimilar_to_sku.add(inner_sku.id)
                dissimilar_for_sku_map[inner_sku.id] = dissimilar_to_inner_sku
                dissimilar_for_sku_map[sku.id] = dissimilar_to_sku
    
    for i, group in groups.items():
        if len(group) > 1:
            print(group)
            for sku_id in group:
                print(sku_id_map[sku_id].title)
            print("------")
    

                
                
            # check for transient relationship




    # We need to create transient handshakes, so the total handshakes <= N(N-1)/2

    # if the score is high, we probe CLI
    # if score is low, we add to disjoint
    # this disjoint

    pass


async def merge_skus(
    sku_ids: List[UUID], active_sku_id: UUID, commit=True, verbose=False
):

    """
    sku_ids: List[UUID]
    active_sku_id: UUID

    The active_sku_id must be there in the list of sku_ids

    """

    session = async_session()

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
            ),
            joinedload(SKU.sku_variants).options(load_only(SKUVariant.id)),
        )
        .where(SKU.id.in_(sku_ids))
    )

    sku_objects: List[SKU] = skus.scalars().all()
    sku_id_map = {sku.id: sku for sku in sku_objects}

    try:
        active_sku = sku_id_map[active_sku_id]
    except:
        print(
            " You need to pass the active_sku_id in sku_ids OR active_sku_id doesn't exist"
        )
        return

    all_sku_variants: List[UUID] = []

    for sku in sku_objects:
        all_sku_variants.extend(sku.sku_variants)

    await session.execute(
        update(SKUVariant)
        .where(SKUVariant.id.in_(all_sku_variants))
        .values(parent_sku_id=active_sku.id)
    )

    # update active_sku fields
    # fields to update: description, price_unit (assert uniform), image_id, quantity_unit (assert uniform), company (assert uniform)
    inactive_skus = list(filter(lambda sku: sku is not active_sku, sku_objects))

    if not active_sku.image_id:
        active_sku.image_id = next(
            filter(lambda sku: sku.image_id is not None, inactive_skus), active_sku
        )

    # assert company is same and not None
    try:
        if not active_sku.company:
            active_sku.company = next(
                filter(lambda sku: sku.company is not None, inactive_skus)
            )

        companies = set(
            map(
                lambda sku: sku.company,
                filter(lambda sku: sku.company is not None, inactive_skus),
            )
        )
        assert len(companies) <= 1
    except:
        print(" The SKU company should be same and exist")
        return

    # TODO: Fix, this doesn't work for hierarchical merges because the description from inactive skus are not considered
    joined_description = " \n ".join(
        filter(lambda x: x is not None, map(lambda x: x.title, inactive_skus))
    )
    active_sku.description += "\n" + joined_description

    # assert price unit is same
    try:
        if not active_sku.price_unit:
            active_sku.price_unit = next(
                filter(lambda sku: sku.price_unit is not None, inactive_skus), None
            )

        price_units = set(
            map(
                lambda sku: sku.price_unit,
                filter(lambda sku: sku.price_unit is not None, inactive_skus),
            )
        )
        assert len(price_units) <= 1
    except:
        print(" The SKU price unit should be same ")
        return
    
     # assert quantity unit is same and not None
    try:
        if not active_sku.quantity_unit:
            active_sku.quantity_unit = next(
                filter(lambda sku: sku.quantity_unit is not None, inactive_skus)
            )

        quantity_units = set(
            map(
                lambda sku: sku.quantity_unit,
                filter(lambda sku: sku.quantity_unit is not None, inactive_skus),
            )
        )
        assert len(quantity_units) <= 1
    except:
        print(" The SKU quantity unit should be same and exist")
        return

    if verbose:
        print(f"Final SKU looks like \n {list(active_sku.__dict__.items())} ")
    if commit:
        session.commit()
    session.close()
    # warehouse_inventories = select(WarehouseInventory).where(WarehouseInventory.sku_variants.op("&&")(all_sku_variants))

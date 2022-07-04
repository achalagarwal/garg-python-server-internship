import uuid
from datetime import datetime
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import SKU, SKUVariant

pytestmark = pytest.mark.asyncio


async def test_sku_merge_works_with_single_primary_sku(
    client: AsyncClient, session: AsyncSession
):
    async def create_objects_in_db(session):
        sku_ids = []
        for i in range(5):
            new_sku = SKU(
                id=uuid.uuid4(),
                title=f"maggi_{i}",
                quantity_unit="units",
                company="TestCompany",
            )
            sku_ids.append(new_sku.id)
            session.add(new_sku)

        for i in range(2):
            new_sku = SKU(
                id=uuid.uuid4(),
                title=f"maggi_old_{i}",
                quantity_unit="units",
                company="TestCompany",
                disabled=True,
                active_parent_sku_id=sku_ids[0],
            )
            session.add(new_sku)

        await session.flush()

        for sku_id in sku_ids:
            for i in range(2):
                new_sku_variant = SKUVariant(
                    parent_sku_id=sku_id, id=uuid.uuid4(), created_at=datetime.utcnow()
                )
                session.add(new_sku_variant)

        await session.commit()
        return sku_ids

    sku_ids = await create_objects_in_db(session)

    # Here we call the new endpoint with 6 skus (including the primary sku id)
    # And also the primary_sku_id

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_id) for sku_id in sku_ids[1:]],
            "primary_sku_id": str(sku_ids[1]),
        },
    )

    assert response.status_code == 200

    await session.commit()

    skus_result = await session.execute(
        select(SKU).options(joinedload(SKU.sku_variants))
    )
    skus: List[SKU] = skus_result.unique().scalars().all()

    unchanged_sku_id = sku_ids[0]
    new_primary_sku_id = sku_ids[1]

    assert len(skus) == 7

    unchanged_sku = next(filter(lambda sku: sku.id == unchanged_sku_id, skus))
    new_primary_sku = next(filter(lambda sku: sku.id == new_primary_sku_id, skus))
    other_skus = list(
        filter(lambda sku: sku not in {unchanged_sku, new_primary_sku}, skus)
    )

    # TODO: Currently we are not updating the skus that were previously disabled, it might make sense to update them
    # TODO: make disabled a non_nullable column, default value is False

    # All the assert statements
    ## Check secondary skus have been disabled and they contain no sku_variants
    assert all(
        sku.disabled is True and len(sku.sku_variants) == 0 for sku in other_skus
    )
    ## Check primary sku has all the previous sku_variants
    assert len(new_primary_sku.sku_variants) == 8
    ## Check active parent sku id has been updated for secondary skus
    assert (
        len(
            list(
                filter(
                    lambda sku: sku.active_parent_sku_id == new_primary_sku_id,
                    other_skus,
                )
            )
        )
        == 3
    )
    assert (
        len(
            list(
                filter(
                    lambda sku: sku.active_parent_sku_id == unchanged_sku_id, other_skus
                )
            )
        )
        == 2
    )

    ## Check that the endpoint does not affect an unrelated SKU
    assert unchanged_sku.disabled is None and len(unchanged_sku.sku_variants) == 2

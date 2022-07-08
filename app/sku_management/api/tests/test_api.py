import uuid
from datetime import datetime
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only

from app.models import SKU, Image, SKUVariant

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

    assert all(
        sku.disabled is True and len(sku.sku_variants) == 0 for sku in other_skus
    )

    assert len(new_primary_sku.sku_variants) == 8

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

    assert unchanged_sku.disabled is None and len(unchanged_sku.sku_variants) == 2


async def test_sku_merge_fails_because_of_multiple_potential_primary_key(
    client: AsyncClient, session: AsyncSession
):
    async def create_objects_in_db_test(session):
        sku_ids = []
        for i in range(3):
            if i == 2:
                new_sku = SKU(
                    id=uuid.uuid4(),
                    title="maggi_2",
                    quantity_unit="units",
                    company="TestCompany",
                    active_parent_sku_id=sku_ids[1],
                )
            else:
                new_sku = SKU(
                    id=uuid.uuid4(),
                    title=f"maggi_{i}",
                    quantity_unit="units",
                    company="TestCompany",
                )
            sku_ids.append(new_sku.id)
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

    sku_ids = await create_objects_in_db_test(session)

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_id) for sku_id in sku_ids[1:]],
            "primary_sku_id": str(sku_ids[0]),
        },
    )
    assert response.status_code == 422
    await session.commit()
    skus_result = await session.execute(
        select(SKU).options(load_only(SKU.disabled), joinedload(SKU.sku_variants))
    )
    skus: List[SKU] = skus_result.unique().scalars().all()

    for i in range(3):
        unchanged_sku_id = sku_ids[i]
        unchanged_sku = next(filter(lambda sku: sku.id == unchanged_sku_id, skus))
        assert unchanged_sku.disabled is None


async def test_sku_merge_fails_because_there_exists_a_primary_sku_which_is_disabled(
    client: AsyncClient, session: AsyncSession
):
    async def create_objects_in_db(session):
        sku_ids = []
        for i in range(3):
            if i == 0:
                new_sku = SKU(
                    id=uuid.uuid4(),
                    title=f"maggi_{i}",
                    quantity_unit="units",
                    company="TestCompany",
                    disabled=True,
                )
            else:
                new_sku = SKU(
                    id=uuid.uuid4(),
                    title=f"maggi_{i}",
                    quantity_unit="units",
                    company="TestCompany",
                )
            sku_ids.append(new_sku.id)
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

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_id) for sku_id in sku_ids[1:]],
            "primary_sku_id": str(sku_ids[0]),
        },
    )
    assert response.status_code == 422

    await session.commit()
    skus_result = await session.execute(select(SKU).options(load_only(SKU.disabled)))
    skus: List[SKU] = skus_result.scalars().all()

    for i in range(3):
        unchanged_sku_id = sku_ids[i]
        unchanged_sku = next(filter(lambda sku: sku.id == unchanged_sku_id, skus))
        if unchanged_sku_id == sku_ids[0]:
            assert unchanged_sku.disabled is True
        else:
            assert unchanged_sku.disabled is None


async def test_sku_merge_fails_because_the_company_or_quantity_unit_mismatched(
    client: AsyncClient, session: AsyncSession
):
    async def create_objects_in_db(session):
        sku_ids = []

        new_sku = SKU(
            id=uuid.uuid4(),
            title="maggi_primary",
            quantity_unit="units",
            company="TestCompany",
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        new_sku = SKU(
            id=uuid.uuid4(),
            title="maggi_secondary",
            quantity_unit="doz",
            company="TestCompany",
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        new_sku = SKU(
            id=uuid.uuid4(),
            title="top_ramen",
            quantity_unit="units",
            company="TestRamen",
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        await session.commit()
        return sku_ids

    sku_ids = await create_objects_in_db(session)

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_ids[1])],
            "primary_sku_id": str(sku_ids[0]),
        },
    )
    assert response.status_code == 422

    await session.commit()

    skus_result = await session.execute(
        select(SKU).options(load_only(SKU.disabled, SKU.active_parent_sku_id))
    )
    skus: List[SKU] = skus_result.scalars().all()

    # dont want to check for primary since its disabled
    for sku in skus:
        assert sku.disabled is None
        assert sku.active_parent_sku_id is None

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_ids[1]), str(sku_ids[0])],
            "primary_sku_id": str(sku_ids[0]),
        },
    )

    assert response.status_code == 422

    await session.commit()

    skus_result = await session.execute(
        select(SKU).options(load_only(SKU.disabled, SKU.active_parent_sku_id))
    )
    skus: List[SKU] = skus_result.scalars().all()

    for sku in skus:
        assert sku.disabled is None
        assert sku.active_parent_sku_id is None


async def test_sku_merge_works_sets_image_id_correctly(
    client: AsyncClient, session: AsyncSession
):
    async def create_objects_in_db(session):
        sku_ids = []

        image_1 = Image(id=uuid.uuid4(), title="TestImage1")
        image_2 = Image(id=uuid.uuid4(), title="TestImage2")

        session.add(image_1)
        session.add(image_2)
        await session.flush()

        new_sku = SKU(
            id=uuid.uuid4(),
            title="maggi_0",
            quantity_unit="units",
            company="TestCompany",
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        new_sku = SKU(
            id=uuid.uuid4(),
            title="maggi_1",
            quantity_unit="units",
            company="TestCompany",
            image_id=image_1.id,
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        new_sku = SKU(
            id=uuid.uuid4(),
            title="maggi_2",
            quantity_unit="units",
            company="TestCompany",
            image_id=image_2.id,
        )
        sku_ids.append(new_sku.id)
        session.add(new_sku)

        await session.commit()
        return sku_ids

    sku_ids = await create_objects_in_db(session)

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_ids[0]), str(sku_ids[1])],
            "primary_sku_id": str(sku_ids[0]),
        },
    )

    assert response.status_code == 200

    await session.commit()

    skus_result = await session.execute(select(SKU))

    skus: List[SKU] = skus_result.scalars().all()

    images_result = await session.execute(select(Image))
    images: List[Image] = images_result.scalars().all()

    assert len(images) == 2

    for sku in skus:
        if sku.id == sku_ids[0]:
            assert (
                next(filter(lambda image: image.id == sku.image_id, images)).title
                == "TestImage1"
            )

    response = await client.post(
        "/api/sku_management/merge_skus",
        json={
            "sku_ids": [str(sku_ids[0]), str(sku_ids[2])],
            "primary_sku_id": str(sku_ids[0]),
        },
    )

    assert response.status_code == 200

    await session.commit()

    skus_result = await session.execute(select(SKU))

    skus: List[SKU] = skus_result.scalars().all()

    images_result = await session.execute(select(Image))
    images: List[Image] = images_result.scalars().all()

    await session.refresh(skus[0])
    await session.refresh(skus[2])

    assert len(images) == 2

    for sku in skus:
        if sku.id == sku_ids[0]:
            assert (
                next(filter(lambda image: image.id == sku.image_id, images)).title
                == "TestImage1"
            )
        else:
            assert sku.disabled is True

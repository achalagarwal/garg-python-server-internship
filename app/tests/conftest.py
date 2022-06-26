import asyncio
from typing import AsyncGenerator

import pytest
from fastapi_users.password import PasswordHelper
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text, inspect
from app.core import config
from app.main import app
from app.models import Base
from app.session import async_engine, async_session
from app.tests import utils

get_password_hash = PasswordHelper().hash

default_user_email = "garg@garghouse.co.in"
default_user_hash = get_password_hash("garg")
superuser_user_email = "contact@@garghouse.co.in"
superuser_user_hash = get_password_hash("contact")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    # loop.close()


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(app=app, base_url="http://doesnt.matter") as client:
        yield client


@pytest.fixture(scope="session")
async def test_db_setup_sessionmaker():
    # assert if we use TEST_DB URL for 100%
    assert config.settings.ENVIRONMENT == "PYTEST"
    assert str(async_engine.url) == config.settings.TEST_SQLALCHEMY_DATABASE_URI

    # always drop and create test db tables between tests session
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # TODO: Create a template database T0 which is a copy of the current database
    return async_session

@pytest.fixture
async def session(test_db_setup_sessionmaker) -> AsyncGenerator[AsyncSession, None]:

    def fn(conn):
        insp = inspect(conn)
        tables = insp.get_table_names()
        query = text("SET session_replication_role = 'replica';")
        conn.execute(query)
        for table in tables:
            if table == "user":
                query = text(f"DELETE FROM public.user")
            else: 
                query = text(f"DELETE FROM {table}")
            conn.execute(query)

        query = text(
            "TRUNCATE TABLE " + ",".join(
                ["public.user" if table == "user" else table for table in tables]
            ) + ";"
        )
        # conn.execute(query)
        query = text("SET session_replication_role = 'origin';")
        conn.execute(query)

    async with test_db_setup_sessionmaker() as session:
        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(fn)


@pytest.fixture
async def default_user(session: AsyncSession):
    return await utils.create_db_user(default_user_email, default_user_hash, session)


@pytest.fixture
async def superuser_user(session: AsyncSession):
    return await utils.create_db_user(
        superuser_user_email, superuser_user_hash, session, is_superuser=True
    )



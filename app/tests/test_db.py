import pytest
from fastapi import Depends
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.api.deps import get_user_db, get_user_manager
from app.schemas import UserDB
from app.tests import utils

get_password_hash = PasswordHelper().hash

# All test coroutines in file will be treated as marked (async allowed).
pytestmark = pytest.mark.asyncio


async def test_create_new_user(session: AsyncSession):
    user = await utils.create_db_user(
        "test@email.address", get_password_hash("test"), session
    )
    user_db = [i async for i in get_user_db()][0]

    stmt = select(user_db.user_table)
    results = [u for (u,) in await session.execute(stmt)]

    assert user.id in {u.id for u in results}

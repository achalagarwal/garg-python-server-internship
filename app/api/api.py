"""
Users and auth routers 'for free' from FastAPI Users.
https://fastapi-users.github.io/fastapi-users/configuration/routers/

You can include more of them + oauth login endpoints.

fastapi_users in defined in deps, because it also
includes useful dependencies.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi_users.password import PasswordHelper
from httpx import AsyncClient
from PIL import Image as PILImage
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import fastapi_users, get_session
from app.core import config, security
from app.models import SKU, Image, Invoice, WarehouseInvoice
from app.schemas import Image as ImageSchema
from app.schemas import UserDB
from app.schemas.utils import DatabaseHasUpdates, LocalDataTimestamps
from app.tests import utils

api_router = APIRouter()
api_router.include_router(
    fastapi_users.get_auth_router(security.AUTH_BACKEND),
    prefix="/auth/jwt",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_register_router(),
    prefix="/auth",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)

client = AsyncClient(base_url="http://localhost:8000/")

get_password_hash = PasswordHelper().hash


@api_router.post("/image", response_model=ImageSchema)
async def post_image(
    image: UploadFile = File(default=None),
    title: str = Form(default=""),
    session: AsyncSession = Depends(get_session),
):
    timestamp = datetime.utcnow()
    id = uuid.uuid4()
    im = PILImage.open(image.file)
    im.save(
        f"{config.settings.FILE_STORE}/images/{id}.png",
        format="png",
        optimize=True,
        quality=50,
    )
    image_dict = {"id": id, "user_id": None, "title": title, "timestamp": timestamp}
    image = Image(**image_dict)
    session.add(image)
    await session.commit()

    return image.__dict__


@api_router.post("/login", response_model=UserDB)
async def login():
    """
    Login an existing user
    """

    raise NotImplementedError(
        "Please remove this statement after implementing this function"
    )


@api_router.post("/signup")
async def signup(
    email: Any = Form(...),
    password: Any = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a user and login
    """

    try:
        await utils.create_db_user(
            email=email, hashed_password=get_password_hash(password), session=session
        )
    except Exception:
        pass

    access_token_res = await client.post(
        "/auth/jwt/login",
        data={
            "username": email,
            "password": password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    token = access_token_res.json()
    access_token = token["access_token"]

    return RedirectResponse(
        url=f"/home?token={access_token}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@api_router.post("/database_updates", response_model=DatabaseHasUpdates)
async def check_database_updates(
    local_data_timestamps: LocalDataTimestamps,
    session: AsyncSession = Depends(get_session),
):
    # TODO: USE READ_UNCOMMITTED FOR NOLOCK MODE
    response = DatabaseHasUpdates(invoice=False, sku=False)
    if local_data_timestamps.invoice is None:
        response.invoice = True

    if local_data_timestamps.sku is None:
        response.sku = True

    if response.invoice is False:
        invoice_table_new_row_result = await session.execute(
            select(Invoice)
            .join(WarehouseInvoice, Invoice.id == WarehouseInvoice.parent_invoice_id)
            .where(
                or_(
                    Invoice.updated_at > local_data_timestamps.invoice,
                    WarehouseInvoice.updated_at > local_data_timestamps.invoice,
                )
            )
            .limit(1)
        )
        invoice_table_new_row = invoice_table_new_row_result.scalar_one_or_none()
        if invoice_table_new_row:
            response.invoice = True

    if response.sku is False:
        sku_table_new_row_result = await session.execute(
            select(SKU).where(SKU.updated_at > local_data_timestamps.sku).limit(1)
        )
        sku_table_new_row = sku_table_new_row_result.one_or_none()
        if sku_table_new_row:
            response.sku = True
    return response

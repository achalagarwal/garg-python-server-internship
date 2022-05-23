
from typing import Any
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse

from fastapi_users.password import get_password_hash

from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import Invoice, UserDB, InvoiceCreate
from app.tests import utils
from sqlalchemy.ext.asyncio import AsyncSession


api_router = APIRouter()
client = AsyncClient(base_url="http://localhost:8000/")


# TODO:  
# Please use multipart/form-data instead of JSON
@api_router.post("/invoice", response_model=Invoice)
async def post_image(
    file: Any = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Insert image in db
    """

    raise NotImplementedError("Please remove this statement after implementing this function")

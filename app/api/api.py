"""
Users and auth routers 'for free' from FastAPI Users.
https://fastapi-users.github.io/fastapi-users/configuration/routers/

You can include more of them + oauth login endpoints.

fastapi_users in defined in deps, because it also
includes useful dependencies.
"""

from typing import Any
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse

from fastapi_users.password import get_password_hash

from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import Image, UserDB
from app.tests import utils
from sqlalchemy.ext.asyncio import AsyncSession


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


# TODO:  
# Please use multipart/form-data instead of JSON
@api_router.post("/image", response_model=Image)
async def post_image(
    file: Any = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Insert image in db
    """

    raise NotImplementedError("Please remove this statement after implementing this function")

@api_router.post("/login", response_model=UserDB)
async def login():
    """
    Login an existing user
    """
    
    raise NotImplementedError("Please remove this statement after implementing this function")


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
        await utils.create_db_user(email=email, hashed_password=get_password_hash(password), session=session)
    except Exception as e:
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

    return RedirectResponse(url=f'/home?token={access_token}', status_code=status.HTTP_303_SEE_OTHER,)





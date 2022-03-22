"""
Users and auth routers 'for free' from FastAPI Users.
https://fastapi-users.github.io/fastapi-users/configuration/routers/

You can include more of them + oauth login endplpoints.

fastapi_users in defined in deps, because it also
includes useful dependencies.
"""

from fastapi import APIRouter, Depends, Request
from fastapi_users import models
from fastapi.templating import Jinja2Templates

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import ImageCreate, Image
from sqlalchemy.ext.asyncio import AsyncSession

templates = Jinja2Templates(directory="app/templates")

page_router = APIRouter()


# TODO:  
# Please use multipart/form-data instead of JSON
@page_router.get("/home")
async def home():
    return templates.TemplateResponse("image_upload.html", {"request": {}})


# TODO:  
# Please use multipart/form-data instead of JSON
@page_router.get("/login-page")
async def home():
    return templates.TemplateResponse("login.html", {"request": {}})

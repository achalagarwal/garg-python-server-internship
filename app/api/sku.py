
from typing import Any, List
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse


from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import SKU as SKUSchema, SKUCreate, SKUInvoice
from app.tests import utils
from app.models import SKU 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from thefuzz import process

sku_router = APIRouter()

client = AsyncClient(base_url="http://localhost:8000/")


# TODO:  
# Please use multipart/form-data instead of JSON
@sku_router.post("/sku", response_model=SKUSchema)
async def post_sku(
    sku: SKUCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Insert sku in db
    """
    
    if sku.image is not None:
        raise NotImplementedError("Please remove this statement after implementing this function")
    
    sku_dict = sku.dict(skip_defaults=True)
    sku_dict["id"] = uuid.uuid4()
    sku = SKU(**sku_dict)
    session.add(sku)
    await session.commit()


@sku_router.get("/sku", response_model=List[SKUSchema])
async def get_sku(session: AsyncSession = Depends(get_session)):
    skus_result = await session.execute(select(SKU))
    skus = skus_result.scalars().all()
    return skus

@sku_router.get("/sku/search", response_model=List[SKUInvoice])
async def search_sku(
    search: str,
    company: str,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):

    # we might not need to complicate this function
    # once we have an index on the "title"
    skus_result = await session.execute(select(SKU).where(SKU.company == company))
    skus = skus_result.scalars().all()
    # skus = session.execute(select(SKU)).filter(
    #         SKU.company == company,
    #     ).with_entities(SKU.title, SKU.id)
    title_mapping = {sku.title: sku for sku in skus}
    matched_sku_titles = map(lambda match: match[0], process.extract(search, map(lambda sku: sku.title, skus), limit=limit))
    matched_skus = [title_mapping[sku_title] for sku_title in matched_sku_titles]

    return matched_skus
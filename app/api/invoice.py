
from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import RedirectResponse

from httpx import AsyncClient

from app.api.deps import fastapi_users, get_session, get_current_user
from app.core import security
from app.schemas import Invoice as InvoiceSchema, UserDB, InvoiceCreate
from app.models import SKU, Invoice
from app.schemas.invoice import Status as InvoiceStatus
from app.tests import utils
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

invoice_router = APIRouter()
client = AsyncClient(base_url="http://localhost:8000/")


@invoice_router.post("/invoice", response_model=InvoiceSchema)
async def post_invoice(
    invoice_data: InvoiceCreate ,
    session: AsyncSession = Depends(get_session),
):

    invoice_dict = invoice_data.dict(skip_defaults=True)
    invoice_dict["id"] = uuid.uuid4()
    invoice_dict["status"] = InvoiceStatus.PENDING.value
    invoice = Invoice(**invoice_dict)
    session.add(invoice)
    await session.commit()
    return invoice

@invoice_router.get("/invoice", response_model=List[InvoiceSchema])
async def get_pending_invoices(page: int = 0, page_size:int = 25, session: AsyncSession = Depends(get_session)):
    invoices_result = await session.execute(select(Invoice).where(
            or_(Invoice.status == InvoiceStatus.PENDING, Invoice.status == InvoiceStatus.PICKING)
        ).order_by(Invoice.created_date).offset(page*page_size).limit(page_size)
    )
    invoices = invoices_result.scalars().all()
    
    for invoice in invoices:
        invoice_items_result = await session.execute(select(SKU).where(SKU.id.in_(invoice.items)))
        invoice.items = invoice_items_result.scalars().all() 

    return invoices


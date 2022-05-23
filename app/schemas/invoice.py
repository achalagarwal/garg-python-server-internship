from re import I
from uuid import UUID
from typing import Any, List, Optional

from fastapi_users import models
from pydantic import UUID4, EmailStr, Field, BaseModel

class InvoiceCreate(BaseModel):   
    # to be updated when we have the company model
    company_display_name: str
    items: List
    deliver_to: str
    invoice_id: str

class Invoice(InvoiceCreate):
    id: UUID
    status: int # Enum: pending, picking, transit, complete
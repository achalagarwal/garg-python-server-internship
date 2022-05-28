"""
SQL Alchemy models declaration.

Note, imported by alembic migrations logic, see `alembic/env.py`
"""

from datetime import datetime
from re import I
from typing import Any, cast
from sqlalchemy.dialects.postgresql import UUID

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import (
    Boolean,
    Column,
    Index,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Date,
    Text,
    delete,
    func,
    select,
    update,
)
from fastapi_users_db_sqlalchemy.guid import GUID
from app.utils import MutableList

Base = cast(Any, declarative_base())

class UserTable(Base, SQLAlchemyBaseUserTable):

    images = relationship("Image", back_populates="user")
    pass

class Image(Base):

    __tablename__ = "image"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    base64 = Column(Text)

    user_id = Column(GUID, ForeignKey("user.id"))
    user = relationship("UserTable", back_populates="images")

class SKU(Base):

    __tablename__ = "sku"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    price = Column(String, nullable=True)
    price_unit = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    weight_unit = Column(String, nullable=True)
    quantity_unit = Column(String) # uom (Unit of Measurement)
    company = Column(String) # change to company_id when we have the company model
    barcode = Column(String)
    image_id = Column(Integer, ForeignKey("image.id"))


class SKUVariant(Base):

    __tablename__ = "sku_variant"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    parent_sku_id = Column(UUID(as_uuid=True), ForeignKey("sku.id"), nullable=False, index=True)
    manufactured_date = Column(Date)
    created_at = Column(DateTime, nullable=False)


class Invoice(Base):

    __tablename__ = "invoice"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    invoice_id = Column(String, nullable=False, index=True)
    items = Column(MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False)
    quantities = Column(MutableList.as_mutable(ARRAY(Integer)), nullable=False)
    company = Column(String, nullable=False) # change to company_id when we have the company model and ensure that all the items are under the same company id
    deliver_to = Column(String)
    status = Column(String, nullable=False)

    created_date = Column(DateTime,  default=datetime.utcnow(), nullable=False)
    Index('idx_orderedby_created_date', created_date, postgresql_using='btree')


class Warehouse(Base):

    __tablename__ = "warehouse"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    # allocations = relationship
    # inventory = relationship
    display_name = Column(String)
    # size and space ...
    # how do we arrange locations?

class WarehouseInventory(Base):

    __tablename__ = "warehouse_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True)
    row = Column(Integer, nullable=False)
    column = Column(Integer, nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouse.id"), nullable=False, index=True)
    sku_variants = Column(MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False)
    quantities = Column(MutableList.as_mutable(ARRAY(Integer)), nullable=False)


    # create a unique constraint on row, column, warehouse_id
    Index('idx_row_column', row, column)
    Index('idx_sku_variants', sku_variants, postgresql_using="gin")



"""
SQL Alchemy models declaration.

Note, imported by alembic migrations logic, see `alembic/env.py`
"""

from datetime import datetime
from multiprocessing.dummy import Array
from re import I
from typing import Any, cast

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from fastapi_users_db_sqlalchemy.guid import GUID
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    delete,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql import func, text

from app.utils import MutableList

_Base = cast(Any, declarative_base())


class Base(_Base):
    __abstract__ = True

    #  FIXME These attributes take priority over subclass attributes with the same name
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=datetime.utcnow(),
    )


class UserTable(Base, SQLAlchemyBaseUserTable):

    images = relationship("Image", back_populates="user")
    pass


class Image(Base):

    __tablename__ = "image"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    title = Column(String, nullable=False)
    base64 = Column(Text)
    timestamp = Column(DateTime)
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
    quantity_unit = Column(String)  # uom (Unit of Measurement)
    company = Column(String)  # change to company_id when we have the company model
    barcode = Column(String)
    image_id = Column(UUID(as_uuid=True), ForeignKey("image.id"))
    sku_variants = relationship("SKUVariant", back_populates="sku")
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=datetime.utcnow(),
        index=True,
    )

    disabled = Column(Boolean, index=True)


class SKUVariant(Base):

    __tablename__ = "sku_variant"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    parent_sku_id = Column(
        UUID(as_uuid=True), ForeignKey("sku.id"), nullable=False, index=True
    )
    sku = relationship("SKU", back_populates="sku_variants")
    manufactured_date = Column(Date)
    created_at = Column(DateTime, nullable=False)


class Invoice(Base):

    __tablename__ = "invoice"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    invoice_id = Column(String, nullable=False, index=True)

    warehouse_invoices = relationship(
        "WarehouseInvoice", back_populates="parent_invoice"
    )

    # sku ids
    items = Column(MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False)
    quantities = Column(MutableList.as_mutable(ARRAY(Integer)), nullable=False)
    company = Column(
        String, nullable=False
    )  # change to company_id when we have the company model and ensure that all the items are under the same company id
    deliver_to = Column(String)
    status = Column(String, nullable=False)
    # type = Column(String, nullable=False)
    # TODO: Rename to Invoice Date
    created_date = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=datetime.utcnow(),
        index=True,
    )

    Index("idx_orderedby_created_date", created_date, postgresql_using="btree")


class WarehouseInvoice(Base):

    __tablename__ = "warehouse_invoice"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    parent_invoice_id = Column(
        UUID(as_uuid=True), ForeignKey("invoice.id"), nullable=False, index=True
    )
    parent_invoice = relationship("Invoice", back_populates="warehouse_invoices")
    status = Column(String, nullable=False)

    warehouse_id = Column(
        UUID(as_uuid=True), ForeignKey("warehouse.id"), nullable=False, index=True
    )

    warehouse_inventories = Column(
        MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False
    )
    sku_variants = Column(
        MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False
    )
    skus = Column(MutableList.as_mutable(ARRAY(UUID(as_uuid=True))), nullable=False)
    quantities = Column(MutableList.as_mutable(ARRAY(Integer)), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    Index(
        "idx_orderedby_created_date_warehouse_invoice",
        created_at,
        postgresql_using="btree",
    )


class WarehouseInvoiceDetails(Base):

    __tablename__ = "warehouse_invoice_details"
    warehouse_invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_invoice.id"),
        nullable=False,
        index=True,
    )

    time_per_item = Column(ARRAY(Float))

    # Array logs for each update
    # These are empty if they are same as the warehouse_invoice.items

    sku_variants = Column(ARRAY(UUID(as_uuid=True)))
    rows = Column(ARRAY(Integer))
    columns = Column(ARRAY(Integer))
    quantities = Column(ARRAY(Integer))

    pass


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
    warehouse_id = Column(
        UUID(as_uuid=True), ForeignKey("warehouse.id"), nullable=False, index=True
    )
    sku_variants = Column(
        MutableList.as_mutable(ARRAY(UUID(as_uuid=True))),
        nullable=False,
        server_default="{}",
    )
    quantities = Column(
        MutableList.as_mutable(ARRAY(Integer)), nullable=False, server_default="{}"
    )
    projected_quantities = Column(
        MutableList.as_mutable(ARRAY(Integer)), nullable=False, server_default="{}"
    )

    # create a unique constraint on row, column, warehouse_id
    Index("idx_row_column", row, column)
    Index("idx_sku_variants", sku_variants, postgresql_using="gin")

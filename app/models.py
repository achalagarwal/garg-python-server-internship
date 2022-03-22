"""
SQL Alchemy models declaration.

Note, imported by alembic migrations logic, see `alembic/env.py`
"""

from typing import Any, cast

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    delete,
    func,
    select,
    update,
)

Base = cast(Any, declarative_base())


class UserTable(Base, SQLAlchemyBaseUserTable):

    images = relationship("Image", back_populates="user")
    pass

class Image(Base):

    __tablename__ = "image"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    base64 = Column(Text)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("UserTable", back_populates="images")

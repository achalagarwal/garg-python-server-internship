from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm.session import sessionmaker

from app.core import config

ENVIRONMENT = config.settings.ENVIRONMENT

sqlalchemy_database_uri = config.settings.DEV_SQLALCHEMY_DATABASE_URI

if "TEST" in ENVIRONMENT:
    sqlalchemy_database_uri = config.settings.TEST_SQLALCHEMY_DATABASE_URI
elif "STAG" in ENVIRONMENT:
    sqlalchemy_database_uri = config.settings.STAGING_SQLALCHEMY_DATABASE_URI
elif "PROD" in ENVIRONMENT:
    sqlalchemy_database_uri = config.settings.PROD_SQLALCHEMY_DATABASE_URI

async_engine = create_async_engine(sqlalchemy_database_uri, pool_pre_ping=True)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

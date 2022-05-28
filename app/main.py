"""
Main FastAPI app instance declaration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.pages import page_router
from app.api.sku import sku_router
from app.api.invoice import invoice_router
from app.api.sku_variants import sku_variant_router
from app.api.warehouse_inventory import warehouse_inventory_router

from app.core import config

app = FastAPI(
    title=config.settings.PROJECT_NAME,
    version=config.settings.VERSION,
    description=config.settings.DESCRIPTION,
    openapi_url="/openapi.json",
    docs_url="/",
)

# Set all CORS enabled origins
if config.settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in config.settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
app.include_router(page_router)
app.include_router(sku_router)
app.include_router(invoice_router)
app.include_router(sku_variant_router)
app.include_router(warehouse_inventory_router)
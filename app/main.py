"""
Main FastAPI app instance declaration
"""

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.pages import page_router
from app.api.sku import sku_router
from app.api.invoice import invoice_router
from app.api.sku_variants import sku_variant_router
from app.api.warehouse_inventory import warehouse_inventory_router
from starlette.requests import Request

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

async def console_log_request_json(request: Request):
    print(await request.json())

app.include_router(api_router)
app.include_router(page_router)
app.include_router(sku_router)
app.include_router(invoice_router)
app.include_router(sku_variant_router)
app.include_router(warehouse_inventory_router, dependencies=[Depends(console_log_request_json)])
app.mount("/static", StaticFiles(directory=config.settings.FILE_STORE), name="file_store")

from fastapi import FastAPI
from sqladmin import Admin, ModelAdmin
from app.session import async_engine
from app.models import UserTable, SKU, SKUVariant, Warehouse, WarehouseInventory, WarehouseInvoice, Invoice, Image

admin = Admin(app, async_engine)


class UserAdmin(ModelAdmin, model=UserTable):
    column_list = [UserTable.id, UserTable.email, UserTable.created_at, UserTable.updated_at]
    column_searchable_list = [UserTable.email, UserTable.created_at]

class SKUAdmin(ModelAdmin, model=SKU):
    column_list = [SKU.id, SKU.title, SKU.description, SKU.company, SKU.updated_at, SKU.created_at, SKU.price, SKU.price_unit, SKU.quantity_unit, SKU.weight, SKU.weight_unit]
    column_searchable_list = [SKU.title, SKU.company, SKU.description]
class SKUVariantAdmin(ModelAdmin, model=WarehouseInventory):
    column_list = [WarehouseInventory.id, WarehouseInventory.row, WarehouseInventory.column, WarehouseInventory.warehouse_id, WarehouseInventory.projected_quantities, WarehouseInventory.quantities, WarehouseInventory.sku_variants]
    column_sortable_list = [WarehouseInventory.row, WarehouseInventory.column, WarehouseInventory.sku_variants]

admin.register_model(UserAdmin)
admin.register_model(SKUAdmin)
admin.register_model(SKUVariantAdmin)
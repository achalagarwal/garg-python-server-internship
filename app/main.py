"""
Main FastAPI app instance declaration
"""

from fastapi import Depends, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelAdmin
from starlette.requests import Request

from app.api.api import api_router
from app.api.invoice import invoice_router
from app.api.pages import page_router
from app.api.sku import sku_router
from app.api.sku_variants import sku_variant_router
from app.api.warehouse_inventory import warehouse_inventory_router
from app.core import config
from app.models import SKU, SKUVariant, UserTable, WarehouseInventory, WarehouseInvoice
from app.session import async_engine
from app.sku_management.api.api import sku_management_router

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
app.include_router(sku_management_router)
app.include_router(
    warehouse_inventory_router, dependencies=[Depends(console_log_request_json)]
)
app.mount(
    "/static", StaticFiles(directory=config.settings.FILE_STORE), name="file_store"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    print(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


admin = Admin(app, async_engine)


class UserAdmin(ModelAdmin, model=UserTable):
    column_list = [
        UserTable.id,
        UserTable.email,
        UserTable.created_at,
        UserTable.updated_at,
    ]
    column_searchable_list = [UserTable.email, UserTable.created_at]


class SKUAdmin(ModelAdmin, model=SKU):
    column_list = [
        SKU.id,
        SKU.title,
        SKU.description,
        SKU.company,
        SKU.updated_at,
        SKU.created_at,
        SKU.price,
        SKU.price_unit,
        SKU.quantity_unit,
        SKU.weight,
        SKU.weight_unit,
    ]
    column_searchable_list = [SKU.title, SKU.company, SKU.description]


class WarehouseInventoryAdmin(ModelAdmin, model=WarehouseInventory):
    column_list = [
        WarehouseInventory.id,
        WarehouseInventory.row,
        WarehouseInventory.column,
    ]
    column_sortable_list = [
        WarehouseInventory.row,
        WarehouseInventory.column,
    ]


class SKUVariantAdmin(ModelAdmin, model=SKUVariant):
    column_list = [SKUVariant.id, SKUVariant.parent_sku_id, SKUVariant.created_at]
    column_sortable_list = [SKUVariant.created_at]


class WarehouseInvoiceAdmin(ModelAdmin, model=WarehouseInvoice):
    column_list = [WarehouseInvoice.parent_invoice_id, WarehouseInvoice.status]
    column_sortable_list = [WarehouseInvoice.status]


admin.register_model(UserAdmin)
admin.register_model(SKUAdmin)
admin.register_model(SKUVariantAdmin)
admin.register_model(WarehouseInventoryAdmin)
admin.register_model(WarehouseInvoiceAdmin)

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
# from starlette.middleware import Middleware
# from starlette.middleware.sessions import SessionMiddleware
# from starlette_admin import DropDown
# from starlette_admin.contrib.sqla import Admin

# from server.adminsuite import add_dashboard
# from database import engine, async_session_maker, cfg_token
# from server.utils import startup
# from models import (
#     # init_storage,
#     Company, Staff, Client,
#     Category, Product, ProductImage, ProductPrice,
#     Post, PostImage,
#     Order, OrderItem,
#     UserActivity, UserInteraction, UserRequest
# )
# from server.adminsuite import (
#     CompanyView, AdminView, StaffView,
#     CategoryView, ProductView, ProductImageView, ProductPriceView,
#     PostView, PostImageView,
#     OrderView, OrderItemView,
#     UserActivityView, UserInteractionView, UserRequestView
# )
# from server.adminsuite.auth import AdminAuthProvider #, StaffAuthProvider

from utils.context import current_staff_id
from loging import setup_srv_logging
from server.routers import include_versioned_routers
# from .utils import start_scheduler, scheduler


# SECRET_KEY = cfg_token()['secret_key']



app = FastAPI(
    title="API for the company",
    description="API for the company",
    version="1.0.0",
)


# Importam toate module signals
try:
    from models import register_all_model_listeners, ListenerRegistrationError
    print("Registering all model listeners...")
    register_all_model_listeners(raise_on_error=True)
    print("All model listeners registered successfully.")
except ListenerRegistrationError as e:
    import logging
    logging.error(f"Listener registration failed: {e}")
    sys.exit(1)


# register_all_model_listeners()

@app.middleware("http")
async def attach_staff_to_ctx(request: Request, call_next):
    staff = getattr(request.state, "user", None)   # depinde de auth logic
    token = current_staff_id.set(staff.id if staff else None)
    try:
        response = await call_next(request)
        return response
    finally:
        current_staff_id.reset(token)

# Montam fisierele statice
app.mount("/static", StaticFiles(directory="static", html=True), name="static")



# *********** START Init app ********************************


# Adaugarea Admin Dashboard
# add_dashboard(app)


# *********** END Init app ********************************




@app.on_event("startup")
async def on_startup():
    """Start + APScheduler"""
    # await startup()
    # start_scheduler()
    # scheduler.start()



@app.get("/")
async def welcome() -> dict:
    return {"message": "404 page not found"}


# Exemplu de endpoint care folosește funcțiile de gestionare a listener-ilor
"""

@app.post("/admin/bulk-import")
async def bulk_import_data():
    # Import în masă de date - dezactivează temporar listener-ii pentru performanță
    
    from app.signals import disable_all_listeners, enable_all_listeners
    
    try:
        # Dezactivează listener-ii pentru operațiunea în masă
        disable_all_listeners()
        
        # Efectuează operațiuni în masă...
        # ...
        
        return {"status": "success", "message": "Import finalizat cu succes"}
    finally:
        # Asigură-te că listener-ii sunt reactivați chiar și în caz de eroare
        enable_all_listeners()

"""




# Înregistrarea dinamica: toate versiunile de API-uri
include_versioned_routers(app)


if __name__ == '__main__':

    loger = setup_srv_logging()
    loger.info('>>> Logging is started <<<')

    import uvicorn
    uvicorn.run("srv:app", port=4040, reload=True)

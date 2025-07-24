# start_server.py

import sys
import io
import logging

from middleware.csrf import CSRFProtectMiddleware

logging.getLogger("watchfiles").setLevel(logging.WARNING)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from loging.srv_logging import setup_srv_logging
from server.routers import include_versioned_routers
from server.dashboard import setup_dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager pentru startup și shutdown.
    """
    # STARTUP - cod executat la pornirea aplicației
    # Poți adăuga aici inițializări

    yield  # Aplicația rulează

    # SHUTDOWN - cod executat la oprirea aplicației
    from cfg.depends import close_db_connections
    await close_db_connections()



app = FastAPI(
    title="API for the company",
    description="API for the company",
    version="1.0.0",
    openapi_url="/ap/openapi.json",
    docs_url="/ap/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # În producție, se vor specifica domeniile exacte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token", "X-Shop-CSRF-Token"],
)

# CSRF Middleware - DUPĂ CORS
app.add_middleware(CSRFProtectMiddleware)

#==>   Mount pentru static aplicație de bază
app.mount("/static",
          StaticFiles(directory="static", html=True),
          name="static"
          )


@app.get("/")
async def welcome() -> dict:
    return {"message": "404 page not found"}


# Înregistrarea dinamica: toate versiunile de API-uri GLOBALE
include_versioned_routers(app)

setup_dashboard(app)

if __name__ == '__main__':
    loger = setup_srv_logging()
    loger.info('>>> Logging is started <<<')

    import uvicorn

    uvicorn.run(
        "server_start:app",
        host="127.0.0.1",
        port=4040,
        reload=True,
        reload_excludes=[
            "logs/*",
            "*.log",
            "__pycache__/*",
            ".git/*",
            ".idea/*"
        ]
    )

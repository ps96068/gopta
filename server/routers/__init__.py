import importlib
import os
from fastapi import FastAPI

def include_versioned_routers(app: FastAPI):
    # Lista de versiuni, corespunde numelor pachetelor din routers
    api_versions = ["v1", "v2"]

    for version in api_versions:
        # Obține calea absolută către pachetul routers/<version>
        package = f"server.routers.{version}"
        package_path = os.path.join(os.path.dirname(__file__), version)

        # Iterăm prin fiecare fișier din directorul versiunii (ex: routers/v1)
        for filename in os.listdir(package_path):
            if filename.endswith(".py") and filename != "__init__.py":
                # Obține numele modulului (ex: routers.v1.user)
                module_name = f"{package}.{filename[:-3]}"

                # Importăm modulul dinamic
                module = importlib.import_module(module_name)
                # Verificăm dacă modulul are un router definit
                if hasattr(module, "router"):
                    # Înregistrăm routerul cu prefixul corespunzător versiunii (ex: /api/v1)
                    app.include_router(module.router, prefix=f"/api/{version}", tags=[version])

# server/dashboard/__init__.py
"""
PCE Admin Dashboard Module

Modul reutilizabil pentru administrare FastAPI applications.
Suportă CRUD complet, import/export, file upload și statistici.
"""

from .router import create_dashboard_router, setup_dashboard
from .config import DashboardConfig

__version__ = "1.0.0"
__all__ = ["create_dashboard_router", "DashboardConfig"]
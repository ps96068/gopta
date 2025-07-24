# middleware/csrf.py
"""
CSRF Protection Middleware pentru întreaga aplicație.
Suportă token-uri CSRF separate pentru Dashboard și Front-end clasic.
"""
from typing import Optional, List, Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders
import secrets
import hmac
import hashlib
from datetime import datetime, timedelta

from cfg import SECRET_KEY

# Configurare
CSRF_SECRET = (SECRET_KEY + "_csrf").encode()
CSRF_TOKEN_LENGTH = 32

# Configurări pentru fiecare frontend
CSRF_CONFIGS = {
    "dashboard": {
        "cookie_name": "csrf_token",  # Păstrăm numele existent
        "header_name": "X-CSRF-Token",  # Header existent
        "form_field": "csrf_token",
        "path": "/dashboard/",
        "max_age": 3600 * 8,  # 8 ore ca auth token
        "samesite": "strict",  # Mai strict pentru admin
        "protected_paths": ["/dashboard/"],
        "exempt_paths": [
            "/dashboard/auth/login",
            "/dashboard/auth/logout",
            "/dashboard-static/",
        ]
    },
    "shop": {
        "cookie_name": "shop_csrf_token",
        "header_name": "X-Shop-CSRF-Token",
        "form_field": "csrf_token",  # Același nume în formular pentru consistență
        "path": "/",
        "max_age": 3600 * 24,  # 24 ore pentru UX mai bun
        "samesite": "lax",  # Mai relaxat pentru shop
        "protected_paths": [
            "/shop/",
            "/cart/",
            "/checkout/",
            "/account/",
            # "/",  # Root pentru viitorul front
        ],
        "exclude_paths": [  # Path-uri care nu vor folosi shop token
            "/dashboard/",
            "/api/v1/bot/",
            "/static/",
            "/ap/",
        ],
        "exempt_paths": [
            "/static/",
            "/api/v1/bot/",  # Webhook-uri Telegram
            "/api/v1/public/",  # API-uri publice
        ]
    }
}

# Paths care nu necesită CSRF deloc
GLOBAL_EXEMPT_PATHS = [
    "/ap/",  # API documentation
    "/favicon.ico",
    "/static/",
    "/health",
    "/metrics",
]


class CSRFProtectMiddleware(BaseHTTPMiddleware):
    """Middleware global pentru protecție CSRF cu suport pentru multiple frontend-uri."""

    def __init__(
            self,
            app,
            secret_key: bytes = CSRF_SECRET,
            configs: Dict = None
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.configs = configs or CSRF_CONFIGS

    async def dispatch(self, request: Request, call_next):
        """Procesează request-ul."""

        # Skip complet pentru WebSocket
        if hasattr(request, 'scope') and request.scope.get('type') == 'websocket':
            return await call_next(request)

        # Skip pentru header Upgrade
        if request.headers.get('upgrade', '').lower() == 'websocket':
            return await call_next(request)

        # Skip pentru path-uri WebSocket
        if '/ws' in request.url.path or request.url.path.endswith('/ws/'):
            return await call_next(request)

        # Determină ce configurare CSRF să folosească
        csrf_config = self._get_csrf_config(request.url.path)

        # Dacă nu necesită protecție, continuă
        if not csrf_config:
            return await call_next(request)

        config_name, config = csrf_config

        if request.url.path.startswith("/dashboard/") and config_name == "shop":
            return await call_next(request)

        needs_protection = self._needs_csrf_protection(
            request.url.path,
            request.method,
            config
        )

        if not needs_protection:
            return await call_next(request)

        # Pentru GET requests, generează și setează token
        if request.method == "GET":
            response = await call_next(request)

            # Verifică dacă există deja token
            existing_token = request.cookies.get(config["cookie_name"])

            # Regenerează token pentru pagina de login după logout
            if self._should_regenerate_token(request, config):
                csrf_token = self._generate_token()
                self._set_csrf_cookie(response, csrf_token, config, request)
                request.state.csrf_token = csrf_token
                request.state.csrf_config = config_name
            elif not existing_token:
                csrf_token = self._generate_token()
                self._set_csrf_cookie(response, csrf_token, config, request)
                request.state.csrf_token = csrf_token
                request.state.csrf_config = config_name
            else:
                request.state.csrf_token = existing_token
                request.state.csrf_config = config_name

            return response

        # Pentru POST, PUT, DELETE, PATCH - verifică token
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Token din cookie
            cookie_token = request.cookies.get(config["cookie_name"])
            if not cookie_token:
                return self._csrf_error(f"CSRF cookie missing")

            # Token din request
            request_token = await self._get_request_token(request, config)

            if not request_token:
                return self._csrf_error(f"CSRF token missing")

            # Validează
            if not self._validate_token(request_token, cookie_token):
                return self._csrf_error(f"Invalid CSRF token")

            # Token valid, continuă
            request.state.csrf_token = cookie_token
            request.state.csrf_config = config_name

        response = await call_next(request)
        return response

    def _get_csrf_config(self, path: str) -> Optional[Tuple[str, Dict]]:
        """Determină care configurare CSRF să folosească bazat pe path."""
        # Check global exempt paths first
        for exempt in GLOBAL_EXEMPT_PATHS:
            if path.startswith(exempt):
                return None

        # Dashboard are prioritate (path specific)
        if path.startswith("/dashboard/"):
            return ("dashboard", self.configs["dashboard"])

        # Shop pentru restul (dar verifică exclude_paths)
        shop_config = self.configs["shop"]
        for exclude in shop_config.get("exclude_paths", []):
            if path.startswith(exclude):
                return None

        # Verifică dacă path-ul necesită protecție shop
        for protected in shop_config["protected_paths"]:
            if path.startswith(protected) or path == "/":
                return ("shop", shop_config)

        return None

    def _needs_csrf_protection(self, path: str, method: str, config: Dict) -> bool:
        """Determină dacă path-ul necesită protecție CSRF."""
        # Skip pentru metode safe
        if method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            return True  # Doar pentru a seta cookie

        # Check exempt paths pentru această configurare
        for exempt in config.get("exempt_paths", []):
            if path.startswith(exempt):
                return False

        # Check exclude paths (pentru shop)
        for exclude in config.get("exclude_paths", []):
            if path.startswith(exclude):
                return False

        # Check protected paths
        for protected in config["protected_paths"]:
            if path.startswith(protected) or (protected == "/" and path == "/"):
                return True

        return False

    def _should_regenerate_token(self, request: Request, config: Dict) -> bool:
        """Verifică dacă trebuie regenerat token-ul."""
        path = request.url.path

        # Regenerează pentru login page după logout
        if path.endswith("/auth/login") and "logout=success" in str(request.url):
            return True

        return False

    def _generate_token(self) -> str:
        """Generează token CSRF nou."""
        return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)

    def _validate_token(self, request_token: str, cookie_token: str) -> bool:
        """Validează token CSRF."""
        return hmac.compare_digest(request_token, cookie_token)

    def _set_csrf_cookie(
            self,
            response,
            token: str,
            config: Dict,
            request: Request
    ):
        """Setează CSRF cookie cu configurarea specifică."""
        response.set_cookie(
            key=config["cookie_name"],
            value=token,
            httponly=True,
            samesite=config["samesite"],
            secure=request.url.scheme == "https",  # Automat pentru HTTPS
            max_age=config["max_age"],
            path=config["path"],
            domain=None  # Folosește domain-ul curent
        )

    async def _get_request_token(self, request: Request, config: Dict) -> Optional[str]:
        """Extrage token din request."""
        # 1. Din header specific
        token = request.headers.get(config["header_name"])
        if token:
            return token

        # 2. Din form data
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                # form_data = await request.form()
                # token = form_data.get(config["form_field"])
                # return token
                return request.cookies.get(config["cookie_name"])
            except Exception:
                pass

        # 3. Din JSON body
        if "application/json" in content_type:
            try:
                body = await request.body()
                request._body = body  # Salvează pentru refolosire
                json_data = await request.json()
                return json_data.get(config["form_field"])
            except Exception:
                pass

        return None

    def _csrf_error(self, detail: str) -> JSONResponse:
        """Returnează eroare CSRF."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": detail,
                "type": "csrf_error"
            }
        )


# Helper functions pentru templates
def get_csrf_token(request: Request) -> str:
    """Obține CSRF token din request."""
    # Încearcă din request.state mai întâi
    token = getattr(request.state, "csrf_token", "")
    if token:
        return token

    # Fallback la cookies bazat pe path
    path = request.url.path
    if path.startswith("/dashboard/"):
        return request.cookies.get("csrf_token", "")  # Token-ul existent pentru dashboard
    else:
        return request.cookies.get("shop_csrf_token", "")


def csrf_input_tag(request: Request) -> str:
    """Generează tag input pentru CSRF."""
    token = get_csrf_token(request)
    return f'<input type="hidden" name="csrf_token" value="{token}">'


def csrf_meta_tag(request: Request) -> str:
    """Generează meta tag pentru CSRF."""
    token = get_csrf_token(request)
    config_name = getattr(request.state, "csrf_config", None)

    # Determină header-ul corect
    if config_name == "dashboard" or request.url.path.startswith("/dashboard/"):
        return f'<meta name="csrf-token" content="{token}" data-header="X-CSRF-Token">'
    else:
        return f'<meta name="csrf-token" content="{token}" data-header="X-Shop-CSRF-Token">'


def get_csrf_header_name(request: Request) -> str:
    """Returnează numele header-ului CSRF pentru request curent."""
    config_name = getattr(request.state, "csrf_config", None)

    if config_name == "dashboard" or request.url.path.startswith("/dashboard/"):
        return "X-CSRF-Token"
    else:
        return "X-Shop-CSRF-Token"
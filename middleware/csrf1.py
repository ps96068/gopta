# middleware/csrf.py
"""
CSRF Protection Middleware pentru întreaga aplicație.
Suportă token-uri CSRF separate pentru Dashboard și Front-end clasic.
"""
from typing import Optional, List
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
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_TOKEN_LENGTH = 32

# Paths care nu necesită CSRF
CSRF_EXEMPT_PATHS = [
    "/ap/",  # API documentation
    "/static/",
    "/dashboard-static/",
    "/favicon.ico",
    "/"  # Root
]

# Paths care necesită CSRF doar pentru anumite metode
CSRF_PROTECTED_PATHS = [
    "/dashboard/",
    "/api/v1/",  # Dacă ai endpoints care modifică date
]


class CSRFProtectMiddleware(BaseHTTPMiddleware):
    """Middleware global pentru protecție CSRF."""

    def __init__(
            self,
            app,
            secret_key: bytes = CSRF_SECRET,
            exempt_paths: List[str] = None,
            protected_paths: List[str] = None,
            cookie_name: str = CSRF_COOKIE_NAME,
            header_name: str = CSRF_HEADER_NAME,
            form_field: str = CSRF_FORM_FIELD
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.exempt_paths = exempt_paths or CSRF_EXEMPT_PATHS
        self.protected_paths = protected_paths or CSRF_PROTECTED_PATHS
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.form_field = form_field

    async def dispatch(self, request: Request, call_next):
        """Procesează request-ul."""

        # Skip complet pentru WebSocket
        # Verifică dacă este WebSocket prin scope type
        if hasattr(request, 'scope') and request.scope.get('type') == 'websocket':
            return await call_next(request)

        # Alternativ/Aditional: verifică header Upgrade
        if request.headers.get('upgrade', '').lower() == 'websocket':
            return await call_next(request)

        # Alternativ/Aditional: verifică dacă path-ul conține /ws
        if '/ws' in request.url.path or request.url.path.endswith('/ws/'):
            return await call_next(request)

        # Verifică dacă path-ul necesită protecție
        path = request.url.path
        needs_protection = self._needs_csrf_protection(path, request.method)

        if not needs_protection:
            return await call_next(request)

        # Pentru GET requests, generează și setează token
        if request.method == "GET":
            response = await call_next(request)

            # Generează token nou dacă nu există
            existing_token = request.cookies.get(self.cookie_name)
            if not existing_token:
                csrf_token = self._generate_token()
                response.set_cookie(
                    key=self.cookie_name,
                    value=csrf_token,
                    httponly=True,
                    samesite="lax",
                    secure=request.url.scheme == "https",
                    max_age=3600 * 4,  # 4 ore
                    path="/"
                )
                # Salvează în request.state pentru templates
                request.state.csrf_token = csrf_token
            else:
                request.state.csrf_token = existing_token

            return response

        # Pentru POST, PUT, DELETE, PATCH - verifică token
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Token din cookie
            cookie_token = request.cookies.get(self.cookie_name)
            if not cookie_token:
                return self._csrf_error("CSRF cookie missing")

            # Token din request
            request_token = await self._get_request_token(request)

            if not request_token:
                return self._csrf_error("CSRF token missing")

            # Validează
            if not self._validate_token(request_token, cookie_token):
                return self._csrf_error("Invalid CSRF token")

            # Token valid, continuă
            request.state.csrf_token = cookie_token

        response = await call_next(request)
        return response

    def _needs_csrf_protection(self, path: str, method: str) -> bool:
        """Determină dacă path-ul necesită protecție CSRF."""
        # Skip pentru metode safe
        if method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            return True  # Doar pentru a seta cookie

        # Check exempt paths
        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return False

        # Check protected paths
        for protected in self.protected_paths:
            if path.startswith(protected):
                return True

        return False

    def _generate_token(self) -> str:
        """Generează token CSRF nou."""
        return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)

    def _validate_token(self, request_token: str, cookie_token: str) -> bool:
        """Validează token CSRF."""
        return hmac.compare_digest(request_token, cookie_token)

    async def _get_request_token(self, request: Request) -> Optional[str]:
        """Extrage token din request."""
        # 1. Din header
        token = request.headers.get(self.header_name)
        if token:
            return token

        # 2. Din form data
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form_data = await request.form()
            token = form_data.get(self.form_field)
            # Important: recreează body pentru următorul middleware
            await request.form()
            return token

        # 3. Din JSON body
        if "application/json" in content_type:
            try:
                body = await request.body()
                request._body = body  # Salvează pentru refolosire
                json_data = await request.json()
                return json_data.get(self.form_field)
            except:
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
    return getattr(request.state, "csrf_token", "") or request.cookies.get(CSRF_COOKIE_NAME, "")


def csrf_input_tag(request: Request) -> str:
    """Generează tag input pentru CSRF."""
    token = get_csrf_token(request)
    return f'<input type="hidden" name="{CSRF_FORM_FIELD}" value="{token}">'


def csrf_meta_tag(request: Request) -> str:
    """Generează meta tag pentru CSRF."""
    token = get_csrf_token(request)
    return f'<meta name="csrf-token" content="{token}">'
# dashboard/routers/auth.py
"""
Router pentru autentificare dashboard.
"""
import pprint
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
import bcrypt

from cfg import get_db, SECRET_KEY, ALGORITHM
from models import AuthUserType, VendorStaff
from models.user import Staff
from services.models.staff_services import StaffService
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from server.dashboard.dependencies import get_current_user_optional # get_current_staff_optional
from services.models.vendor_staff_service import VendorStaffService

auth_router = APIRouter()

templates = Jinja2Templates(directory="server/dashboard/templates")
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


# @auth_router.get("/login", response_class=HTMLResponse)
# async def login_page(
#         request: Request,
#         next: Optional[str] = None,
#         error: Optional[str] = None,
#         staff: Optional[Staff] = Depends(get_current_staff_optional)
# ):
#     """Afișează pagina de login."""
#     # Dacă e deja autentificat, redirect
#     print(f"Login page accessed with next={next} and error={error}")
#     if staff:
#         return RedirectResponse(url="/dashboard/home", status_code=302)
#
#     return templates.TemplateResponse(
#         "auth/login.html",
#         {
#             "request": request,
#             "next": next or "/dashboard/home",
#             "error": error,
#             "dashboard_title": "PCE Admin - Login"
#         }
#     )
#
#
# @auth_router.post("/login")
# async def login(
#         request: Request,
#         response: Response,
#         email: str = Form(...),
#         password: str = Form(...),
#         remember_me: bool = Form(False),
#         next: str = Form("/dashboard/home"),
#         db: AsyncSession = Depends(get_db)
# ):
#     """Procesează login."""
#     try:
#         # Verifică credențiale
#         staff = await StaffService.authenticate(db, email, password)
#
#         if not staff:
#             print(f"++++++++++++++++++ Failed login attempt for email: {email}")
#             # Redirect înapoi cu eroare
#             return RedirectResponse(
#                 url=f"/dashboard/auth/login?error=invalid_credentials&next={next}",
#                 status_code=302
#             )
#
#         # Creează token JWT
#         expire_minutes = 60 * 24 * 7 if remember_me else 60 * 8  # 7 zile sau 8 ore
#         access_token_expires = timedelta(minutes=expire_minutes)
#         access_token = create_access_token(
#             data={"sub": str(staff.id)},
#             expires_delta=access_token_expires
#         )
#
#         # Setează cookie
#         response = RedirectResponse(url=next, status_code=302)
#         response.set_cookie(
#             key="dashboard_token",
#             value=access_token,
#             max_age=expire_minutes * 60,  # în secunde
#             httponly=True,
#             samesite="lax",
#             secure=request.url.scheme == "https"
#         )
#
#         return response
#
#     except Exception as e:
#         # Log error
#         print(f"Login error: {e}")
#         return RedirectResponse(
#             url=f"/dashboard/auth/login?error=server_error&next={next}",
#             status_code=302
#         )
#
#
# @auth_router.get("/logout")
# async def logout(
#         request: Request,
#         response: Response
# ):
#     """Logout și redirect la login."""
#     response = RedirectResponse(url="/dashboard/auth/login", status_code=302)
#     response.delete_cookie(key="dashboard_token")
#     return response
#
# @auth_router.post("/logout")
# async def logout_post(
#     request: Request,
#     response: Response
# ):
#     """Logout POST pentru CSRF protection."""
#     response = RedirectResponse(url="/dashboard/auth/login?logout=success", status_code=302)
#     response.delete_cookie(key="dashboard_token")
#     return response







# Utility functions


@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(
        request: Request,
        next: Optional[str] = None,
        error: Optional[str] = None,
        user: Optional[Union[Staff, VendorStaff]] = Depends(get_current_user_optional)
):
    """Afișează pagina de login unificată."""
    pprint.pprint("************** LOGIN Get **************")
    # Dacă e deja autentificat, redirect bazat pe tip
    if user:
        if isinstance(user, Staff):
            return RedirectResponse(url="/dashboard/staff/home", status_code=302)
        else:  # VendorStaff
            return RedirectResponse(url="/dashboard/vendor/home", status_code=302)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "next": next or "/dashboard/home",
            "error": error,
            "dashboard_title": "PCE Dashboard - Login"
        }
    )



@auth_router.post("/login")
async def login(
        request: Request,
        response: Response,
        email: str = Form(...),
        password: str = Form(...),
        remember_me: bool = Form(False),
        next: str = Form("/dashboard/home"),
        db: AsyncSession = Depends(get_db)
):
    """
    Procesează login - detectează automat tipul de utilizator.
    Caută mai întâi în Staff, apoi în VendorStaff.
    """

    print("************** LOGIN Post **************")


    try:
        user = None
        user_type = None

        # 1. Încearcă să autentifice ca Staff
        staff = await StaffService.authenticate(db, email, password)
        if staff:
            user = staff
            user_type = AuthUserType.STAFF
        else:
            # 2. Încearcă să autentifice ca VendorStaff
            vendor_staff = await VendorStaffService.authenticate(db, email, password)
            if vendor_staff:
                user = vendor_staff
                user_type = AuthUserType.VENDOR

        if not user:
            # Nu s-a găsit utilizatorul în niciun tabel
            return RedirectResponse(
                url=f"/dashboard/auth/login?error=invalid_credentials&next={next}",
                status_code=302
            )

        # Creează token JWT cu tipul de user
        expire_minutes = 60 * 24 * 7 if remember_me else 60 * 8  # 7 zile sau 8 ore
        access_token_expires = timedelta(minutes=expire_minutes)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "user_type": user_type,
                "vendor_company_id": user.company_id if user_type == AuthUserType.VENDOR else None
            },
            expires_delta=access_token_expires
        )

        # Determină URL-ul de redirect bazat pe tipul de utilizator
        if user_type == AuthUserType.VENDOR:
            default_redirect = "/dashboard/vendor/home"
        else:  # STAFF
            default_redirect = "/dashboard/staff/home"

        # Verifică parametrul next
        if next and next not in ["/dashboard/", "/dashboard"]:
            # Evită dublarea /home
            if next.endswith("/home") or next.endswith("/home/"):
                redirect_url = default_redirect
            # Pentru staff
            elif user_type == AuthUserType.STAFF:
                if next.startswith("/dashboard/vendor/"):
                    # Nu permite acces la vendor URLs pentru staff
                    redirect_url = default_redirect
                elif next.startswith("/dashboard/staff/"):
                    # URL deja corect format
                    redirect_url = next
                elif next.startswith("/dashboard/"):
                    # Convertește generic dashboard URL la staff URL
                    redirect_url = next.replace("/dashboard/", "/dashboard/staff/")
                else:
                    redirect_url = default_redirect
            # Pentru vendor
            elif user_type == AuthUserType.VENDOR:
                if next.startswith("/dashboard/vendor/"):
                    redirect_url = next
                else:
                    redirect_url = default_redirect
            else:
                redirect_url = default_redirect
        else:
            redirect_url = default_redirect

        # Normalizează URL-ul (elimină slash-uri multiple)
        redirect_url = redirect_url.rstrip('/').replace('//', '/')

        # Setează cookie
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="dashboard_token",
            value=access_token,
            max_age=expire_minutes * 60,  # în secunde
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https"
        )

        return response

    except Exception as e:
        print(f"Login error: {e}")
        return RedirectResponse(
            url=f"/dashboard/auth/login?error=server_error&next={next}",
            status_code=302
        )


@auth_router.get("/logout")
async def logout(
        request: Request,
        response: Response
):
    """Logout și redirect la login."""
    response = RedirectResponse(url="/dashboard/auth/login?logout=success", status_code=302)
    response.delete_cookie(key="dashboard_token")
    response.delete_cookie(key="csrf_token")
    return response


@auth_router.post("/logout")
async def logout_post(
        request: Request,
        response: Response
):
    """Logout POST pentru CSRF protection."""
    response = RedirectResponse(url="/dashboard/auth/login?logout=success", status_code=302)
    response.delete_cookie(key="dashboard_token")
    response.delete_cookie(key="csrf_token")
    return response




def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creează JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifică parola cu bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash password cu bcrypt."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
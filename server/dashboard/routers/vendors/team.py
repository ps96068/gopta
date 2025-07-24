# server/dashboard/routers/vendors/team.py
"""
Router pentru gestionarea echipei vendor (doar pentru admin).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import VendorStaff, VendorRole
from server.dashboard.dependencies import get_current_vendor_staff, get_template_context, require_role
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.vendor_staff_service import VendorStaffService

vendor_team_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/vend")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@vendor_team_router.get("/", response_class=HTMLResponse)
async def vendor_team_list(
        request: Request,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă membri echipă vendor (doar admin)."""

    # Verifică că e admin
    if vendor_staff.role != VendorRole.ADMIN:
        raise HTTPException(status_code=403, detail="Acces permis doar pentru admin")

    # Get team members
    result = await db.execute(
        select(VendorStaff)
        .where(VendorStaff.company_id == vendor_staff.company_id)
        .order_by(VendorStaff.role, VendorStaff.first_name)
    )
    team_members = result.scalars().all()

    # Count by role
    admin_count = sum(1 for m in team_members if m.role == VendorRole.ADMIN)
    manager_count = sum(1 for m in team_members if m.role == VendorRole.MANAGER)
    active_count = sum(1 for m in team_members if m.is_active)
    inactive_count = len(team_members) - active_count


    context = await get_template_context(request, vendor_staff, db)
    context.update({
        "page_title": "Echipa Mea",
        "team_members": team_members,
        "total_members": len(team_members),
        "admin_count": admin_count,
        "manager_count": manager_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "current_user_id": vendor_staff.id
    })

    return templates.TemplateResponse("team/list.html", context)


@vendor_team_router.get("/create", response_class=HTMLResponse)
async def vendor_team_create_form(
        request: Request,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Formular adăugare membru echipă."""

    if vendor_staff.role != VendorRole.ADMIN:
        raise HTTPException(status_code=403, detail="Acces permis doar pentru admin")

    context = await get_template_context(request, vendor_staff, db)
    context.update({
        "page_title": "Adaugă Membru Echipă",
        "roles": list(VendorRole)
    })

    return templates.TemplateResponse("team/form.html", context)


@vendor_team_router.post("/create")
async def vendor_team_create(
        email: str = Form(...),
        password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: Optional[str] = Form(None),
        role: str = Form(...),
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Creează membru echipă nou."""

    if vendor_staff.role != VendorRole.ADMIN:
        raise HTTPException(status_code=403)

    try:
        # Check if email exists
        existing = await VendorStaffService.get_by_email(db, email)
        if existing:
            return RedirectResponse(
                url="/dashboard/vendor/team/create?error=email_exists",
                status_code=303
            )

        # Create new member
        new_member = await VendorStaffService.create(
            db=db,
            company_id=vendor_staff.company_id,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=VendorRole[role.upper()],
            phone=phone
        )

        return RedirectResponse(
            url="/dashboard/vendor/team?success=member_added",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating team member: {e}")
        return RedirectResponse(
            url="/dashboard/vendor/team/create?error=create_failed",
            status_code=303
        )


@vendor_team_router.post("/{member_id}/toggle-active")
async def vendor_team_toggle_active(
        member_id: int,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Activează/Dezactivează membru echipă."""

    if vendor_staff.role != VendorRole.ADMIN:
        raise HTTPException(status_code=403)

    # Nu poți să te dezactivezi singur
    if member_id == vendor_staff.id:
        return RedirectResponse(
            url="/dashboard/vendor/team?error=cannot_deactivate_self",
            status_code=303
        )

    result = await db.execute(
        select(VendorStaff).where(
            VendorStaff.id == member_id,
            VendorStaff.company_id == vendor_staff.company_id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404)

    member.is_active = not member.is_active
    await db.commit()

    return RedirectResponse(
        url="/dashboard/vendor/team?success=status_updated",
        status_code=303
    )


@vendor_team_router.post("/{member_id}/delete")
async def vendor_team_delete(
        member_id: int,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Șterge membru echipă (soft delete)."""

    if vendor_staff.role != VendorRole.ADMIN:
        raise HTTPException(status_code=403)

    # Nu poți să te ștergi singur
    if member_id == vendor_staff.id:
        return RedirectResponse(
            url="/dashboard/vendor/team?error=cannot_delete_self",
            status_code=303
        )

    # Verifică că e din aceeași companie
    result = await db.execute(
        select(VendorStaff).where(
            VendorStaff.id == member_id,
            VendorStaff.company_id == vendor_staff.company_id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404)

    # Verifică să nu rămână fără admin
    if member.role == VendorRole.ADMIN and member.is_active:
        active_admin_count = await db.execute(
            select(func.count(VendorStaff.id)).where(
                VendorStaff.company_id == vendor_staff.company_id,
                VendorStaff.role == VendorRole.ADMIN,
                VendorStaff.is_active == True,
                VendorStaff.id != member_id
            )
        )
        if active_admin_count.scalar() == 0:
            return RedirectResponse(
                url="/dashboard/vendor/team?error=need_at_least_one_admin",
                status_code=303
            )

    # Soft delete - păstrăm datele dar marcăm ca șters
    member.is_active = False
    member.email = f"deleted_{member.id}_{member.email}"  # Previne conflicte de email
    await db.commit()

    return RedirectResponse(
        url="/dashboard/vendor/team?success=member_deleted",
        status_code=303
    )




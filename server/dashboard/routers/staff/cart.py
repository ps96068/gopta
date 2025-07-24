# server/dashboard/routers/cart.py
"""
Router pentru gestionarea coșurilor de cumpărături.
"""

from __future__ import annotations
import logging
logger = logging.getLogger("uvicorn.error")


import traceback
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from jinja2 import Environment

from cfg import get_db
from models import Cart, CartItem, Client, Product, Order, Category, OrderStatus
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only, days_ago
from services.models.cart_service import CartService
from services.models.order_service import OrderService
from server.dashboard.utils import CART_ITEMS_ROWS


cart_router = APIRouter()
env = Environment()
j_template = env.from_string(CART_ITEMS_ROWS)

templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only
templates.env.filters['days_ago'] = days_ago


@cart_router.get("/", response_class=HTMLResponse)
async def cart_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        days_old: Optional[int] = None,
        client_id: Optional[int] = Query(None),  # ADĂUGAT: pentru filtrare după client
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă coșuri active cu statistici - doar coșuri cu produse."""

    # Query de bază - doar coșurile care au items
    query = select(Cart).options(
        selectinload(Cart.client),
        selectinload(Cart.items).selectinload(CartItem.product)
    ).join(CartItem).distinct()

    # Filtre
    filters = []

    if client_id:  # ADĂUGAT: filtru după client
        filters.append(Cart.client_id == client_id)

    if search:
        query = query.join(Client).where(
            or_(
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%")
            )
        )

    if days_old:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        filters.append(Cart.updated_at < cutoff_date)

    if filters:
        query = query.where(and_(*filters))

    # ADĂUGAT: Obține informații client dacă se filtrează după client
    filtered_client = None
    if client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        filtered_client = client_result.scalar_one_or_none()

    # Total pentru paginare - doar coșuri cu items
    total_query = select(func.count(Cart.id.distinct())).select_from(Cart).join(CartItem)

    if client_id:  # ADĂUGAT: filtru pentru total
        total_query = total_query.where(Cart.client_id == client_id)

    if search:
        total_query = total_query.join(Client).where(
            or_(
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%")
            )
        )
    if filters and not client_id:  # Evită dublarea filtrului client_id
        total_query = total_query.where(and_(*filters))
    elif filters and client_id:  # Aplică doar filtrele non-client_id
        non_client_filters = [f for f in filters if str(f) != f"cart.client_id = :client_id_1"]
        if non_client_filters:
            total_query = total_query.where(and_(*non_client_filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare și paginare
    offset = (page - 1) * per_page
    query = query.order_by(Cart.updated_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    carts = result.scalars().all()

    # Calculează totale pentru fiecare coș
    cart_totals = {}
    for cart in carts:
        total_amount = sum(
            float(item.price_snapshot) * item.quantity
            for item in cart.items
        )
        cart_totals[cart.id] = {
            'total': total_amount,
            'items_count': len(cart.items),
            'total_quantity': sum(item.quantity for item in cart.items)
        }

    # Stats generale - ajustează pentru filtrul de client
    if client_id:
        # Statistici specifice clientului
        total_carts_query = select(func.count(Cart.id.distinct())).select_from(Cart).join(CartItem).where(Cart.client_id == client_id)
        abandoned_date = datetime.utcnow() - timedelta(days=7)
        abandoned_carts = await db.execute(
            select(func.count(Cart.id.distinct()))
            .select_from(Cart)
            .join(CartItem)
            .where(and_(Cart.client_id == client_id, Cart.updated_at < abandoned_date))
        )
        # Coșuri ale clientului cu items
        client_carts_result = await db.execute(
            select(Cart).options(selectinload(Cart.items)).join(CartItem).where(Cart.client_id == client_id).distinct()
        )
        client_carts = client_carts_result.scalars().all()
        total_value = sum(
            sum(float(item.price_snapshot) * item.quantity for item in cart.items)
            for cart in client_carts
        )
    else:
        # Statistici globale
        total_carts_query = select(func.count(Cart.id.distinct())).select_from(Cart).join(CartItem)
        abandoned_date = datetime.utcnow() - timedelta(days=7)
        abandoned_carts = await db.execute(
            select(func.count(Cart.id.distinct()))
            .select_from(Cart)
            .join(CartItem)
            .where(Cart.updated_at < abandoned_date)
        )
        # Toate coșurile cu items
        all_carts_result = await db.execute(
            select(Cart).options(selectinload(Cart.items)).join(CartItem).distinct()
        )
        all_carts = all_carts_result.scalars().all()
        total_value = sum(
            sum(float(item.price_snapshot) * item.quantity for item in cart.items)
            for cart in all_carts
        )

    total_carts_result = await db.execute(total_carts_query)
    total_carts_count = total_carts_result.scalar() or 0
    abandoned_count = abandoned_carts.scalar() or 0

    total_pages = (total + per_page - 1) // per_page

    # ADĂUGAT: Logică navigare pentru întoarcerea la client
    back_url = None
    back_text = None
    page_title = "Coșuri de Cumpărături"

    if filtered_client:
        back_url = f"/dashboard/staff/client/{client_id}"
        back_text = f"Înapoi la {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"
        page_title = f"Coșuri - {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"

    context = await get_template_context(request, staff)
    context.update({
        "page_title": page_title,
        "carts": carts,
        "cart_totals": cart_totals,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": int(total_pages),
        "total_carts": total_carts_count,
        "abandoned_carts": abandoned_count,
        "total_value": total_value,
        "search_query": search,
        "client_filter": client_id,  # ADĂUGAT
        "filtered_client": filtered_client,  # ADĂUGAT
        "back_url": back_url,  # ADĂUGAT
        "back_text": back_text,  # ADĂUGAT
        "datetime": datetime,
        "days_old_filter": days_old
    })

    return templates.TemplateResponse("cart/list.html", context)


@cart_router.get("/create", response_class=HTMLResponse)
async def cart_create_form(
        request: Request,
        client_id: Optional[int] = Query(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Formular pentru selectare client - pasul 1."""

    # Get client if specified
    client = None
    if client_id:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

    # Get all active clients
    clients_result = await db.execute(
        select(Client)
        .where(Client.is_active == True)
        .order_by(Client.first_name, Client.last_name)
    )
    clients = clients_result.scalars().all()

    # Get order counts for each client
    client_orders_count = {}
    for c in clients:
        orders_count = await db.execute(
            select(func.count(Order.id)).where(Order.client_id == c.id)
        )
        client_orders_count[c.id] = orders_count.scalar() or 0

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Coș Nou - Selectare Client",
        "client": client,
        "clients": clients,
        "client_orders_count": client_orders_count
    })

    return templates.TemplateResponse("cart/select_client.html", context)


@cart_router.post("/create")
async def cart_create_redirect(
        client_id: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Redirecționează către selectarea produselor - pasul 2."""

    # Verifică dacă clientul există
    client_result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        return RedirectResponse(
            url="/dashboard/staff/cart/create?error=client_not_found",
            status_code=303
        )

    # Redirecționează către pagina de selectare produse
    return RedirectResponse(
        url=f"/dashboard/staff/cart/select-products?client_id={client_id}",
        status_code=303
    )


@cart_router.get("/select-products", response_class=HTMLResponse)
async def select_products(
        request: Request,
        client_id: int = Query(...),
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Pagină pentru selectarea produselor - pasul 2."""

    # Get client
    client_result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client negăsit")

    # Get products for selection
    products_query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.prices),
        selectinload(Product.images)
    ).where(
        and_(
            Product.is_active == True,
            Product.in_stock == True
        )
    )

    if category_id:
        products_query = products_query.where(Product.category_id == category_id)

    if search:
        products_query = products_query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    products_result = await db.execute(products_query.limit(50))
    products = products_result.scalars().all()

    # Get categories for filter
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Selectare Produse pentru {client.first_name or 'Client'} {client.last_name or ''}",
        "client": client,
        "products": products,
        "categories": categories,
        "category_filter": category_id,
        "search_query": search
    })

    return templates.TemplateResponse("cart/select_products.html", context)


@cart_router.post("/create-with-products")
async def create_cart_with_products(
        request: Request,
        client_id: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Creează coș cu produsele selectate."""

    # Get form data
    form = await request.form()

    logger.info(f"Form data received: {dict(form)}")

    # Colectează produsele selectate
    selected_products = []
    for key, value in form.items():
        if key.startswith("product_") and value:
            product_id = int(key.replace("product_", ""))
            quantity = int(value)
            if quantity > 0:
                selected_products.append((product_id, quantity))

    # Dacă nu s-au selectat produse, redirecționează înapoi
    if not selected_products:
        return RedirectResponse(
            url=f"/dashboard/staff/cart/select-products?client_id={client_id}&error=no_products",
            status_code=303
        )

    try:
        # Creează coșul
        cart = await CartService.get_or_create_cart(
            db=db,
            client_id=client_id,
            session_id=f"dashboard-{staff.id}-{datetime.utcnow().timestamp()}"
        )

        # Get client pentru a determina prețul
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = client_result.scalar_one()

        # Adaugă produsele în coș
        for product_id, quantity in selected_products:
            await CartService.add_item(
                db=db,
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                user_status=client.status
            )

        # Actualizează totalul coșului
        cart.total_amount = await CartService.get_cart_total(db=db, cart_id=cart.id)

        # Redirecționează către lista de coșuri
        return RedirectResponse(
            url="/dashboard/staff/cart?success=cart_created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating cart with products: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/cart/select-products?client_id={client_id}&error=create_failed",
            status_code=303
        )


@cart_router.get("/{cart_id}", response_class=HTMLResponse)
async def cart_detail(
        request: Request,
        cart_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii coș cu produse și opțiuni."""

    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.client),
            selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.category)
        )
    )
    cart = result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Coș negăsit")

    # Calculează total
    cart_total = sum(
        float(item.price_snapshot) * item.quantity
        for item in cart.items
    )

    # Verifică dacă clientul are deja o comandă activă
    # active_order = await db.execute(
    #     select(Order)
    #     .where(
    #         and_(
    #             Order.client_id == cart.client_id,
    #             Order.status.in_([OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.PROCESSING])
    #         )
    #     )
    #     .order_by(Order.created_at.desc())
    #     .limit(1)
    # )
    # has_active_order = active_order.scalar_one_or_none() is not None

    # Statistici client
    client_orders = await db.execute(
        select(func.count(Order.id)).where(Order.client_id == cart.client_id)
    )
    client_orders_count = client_orders.scalar() or 0

    cart_age = days_ago(cart.updated_at)

    # Obține ofertele active pentru acest coș
    active_quotes = await CartService.get_active_quotes(db, cart.id)

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Coș #{cart.id}",
        "cart": cart,
        "cart_total": cart_total,
        "cart_age": cart_age,
        "active_quotes": active_quotes,
        "user": staff,  # Pentru can_create în template
        # "has_active_order": has_active_order,
        # "client_orders_count": client_orders_count
    })

    return templates.TemplateResponse("cart/detail.html", context)



@cart_router.get("/manage/{cart_id}", response_class=HTMLResponse)
async def manage_cart(
        request: Request,
        cart_id: int,
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Pagină pentru gestionarea produselor din coș."""

    # Convert category_id to int if possible, else None
    try:
        category_id_int = int(category_id) if category_id else None
    except ValueError:
        category_id_int = None


    # Obține coșul cu toate relațiile
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.client),
            selectinload(Cart.items).selectinload(CartItem.product),
            selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.category)
        )
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Coș negăsit")

    cart_client_id = cart.client_id




    # Produse disponibile pentru adăugare
    products_query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.prices),
        selectinload(Product.images)
    ).where(
        and_(
            Product.is_active == True,
            Product.in_stock == True
        )
    )
    if category_id_int:
        products_query = products_query.where(Product.category_id == category_id_int)
    if search:
        products_query = products_query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )
    products_result = await db.execute(products_query.limit(50))
    products = products_result.scalars().all()

    # Categorii pentru filtrare
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    # Total coș
    cart_total = sum(
        float(item.price_snapshot) * item.quantity
        for item in cart.items
    )
    # Vechime coș
    days_old = days_ago(cart.updated_at)

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Gestionează Coș #{cart.id}",
        "cart": cart,
        "cart_total": cart_total,
        "products": products,
        "categories": categories,
        "category_filter": category_id_int,
        "search_query": search,
        "days_old": days_old,
        "client": cart_client_id
    })
    return templates.TemplateResponse("cart/manage.html", context)




@cart_router.get("/{cart_id}/edit", response_class=HTMLResponse)
async def edit_cart(
        request: Request,
        cart_id: int,
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Pagină pentru editare produse în coș existent."""

    # Get cart with client and items
    cart_result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.client),
            selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.category)
        )
    )
    cart = cart_result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Coș negăsit")

    # Get products for selection
    products_query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.prices),
        selectinload(Product.images)
    ).where(
        and_(
            Product.is_active == True,
            Product.in_stock == True
        )
    )

    if category_id:
        products_query = products_query.where(Product.category_id == category_id)

    if search:
        products_query = products_query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    products_result = await db.execute(products_query.limit(50))
    products = products_result.scalars().all()

    # Get categories for filter
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    # Calculate cart total
    cart_total = sum(
        float(item.price_snapshot) * item.quantity
        for item in cart.items
    )

    # Calculate days old for cart
    cart_days_old = days_ago(cart.updated_at)

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Editare Coș - {cart.client.first_name or 'Client'} {cart.client.last_name or ''}",
        "cart": cart,
        "cart_total": cart_total,
        "products": products,
        "categories": categories,
        "category_filter": category_id,
        "search_query": search,
        "days_old": cart_days_old
    })

    return templates.TemplateResponse("cart/edit.html", context)


@cart_router.post("/{cart_id}/update-item/{item_id}")
async def update_cart_item(
        cart_id: int,
        item_id: int,
        quantity: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează cantitatea unui item din coș."""

    try:
        if quantity <= 0:
            # Șterge item-ul
            await CartService.update_quantity(db, item_id, 0)
        else:
            # Actualizează cantitatea
            await CartService.update_quantity(db, item_id, quantity)

        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?success=item_updated",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=update_failed",
            status_code=303
        )


@cart_router.post("/{cart_id}/remove-item/{item_id}")
async def remove_cart_item(
        cart_id: int,
        item_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge un item din coș."""

    try:
        await CartService.update_quantity(db, item_id, 0)

        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?success=item_removed",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=remove_failed",
            status_code=303
        )


@cart_router.post("/{cart_id}/clear")
async def clear_cart(
        cart_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Golește complet coșul."""

    try:
        await CartService.clear_and_delete_cart(db, cart_id)

        return RedirectResponse(
            url="/dashboard/staff/cart?success=cart_cleared",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=clear_failed",
            status_code=303
        )




@cart_router.post("/{cart_id}/delete")
async def delete_cart(
        cart_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge coșul complet din sistem (Cart + CartItems)."""

    try:
        # Folosim o tranzacție explicită
        # async with db.begin():
            # Mai întâi ștergem toate CartItems

        cart = await db.get(Cart, cart_id)


        if cart:
            await db.delete(cart)
            await db.commit()




        print(f"Cart {cart_id} deleted successfully")

        return RedirectResponse(
            url="/dashboard/staff/cart?success=cart_deleted",
            status_code=303
        )

    except Exception as e:
        print(f"Error deleting cart {cart_id}: {e}")
        traceback.print_exc()
        await db.rollback()
        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=delete_failed",
            status_code=303
        )


@cart_router.post("/{cart_id}/convert-to-order")
async def convert_to_order(
        cart_id: int,
        client_note: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Convertește coșul în comandă."""

    try:
        # Verifică dacă coșul are items
        result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items))
        )
        cart = result.scalar_one_or_none()

        if not cart or not cart.items:
            return RedirectResponse(
                url=f"/dashboard/staff/cart/{cart_id}?error=empty_cart",
                status_code=303
            )

        # Creează comanda
        order = await OrderService.create_from_cart(
            db=db,
            cart_id=cart_id,
            client_note=client_note
        )

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order.id}?success=order_created",
            status_code=303
        )

    except Exception as e:
        print(f"Error converting cart to order: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=conversion_failed",
            status_code=303
        )


# AJAX endpoints pentru edit
@cart_router.post("/add-product-ajax")
async def add_product_to_cart_ajax(
        cart_id: int = Form(...),
        product_id: int = Form(...),
        quantity: int = Form(1),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Adaugă produs în coș (AJAX)."""

    try:
        # Get cart with client
        cart_result = await db.execute(
            select(Cart).where(Cart.id == cart_id).options(selectinload(Cart.client))
        )
        cart = cart_result.scalar_one_or_none()

        if not cart:
            return JSONResponse(
                status_code=404,
                content={"error": "Coș negăsit"}
            )

        # Add item to cart
        item = await CartService.add_item(
            db=db,
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            user_status=cart.client.status
        )

        # Get product details
        product_result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one()

        # Get updated cart
        cart_result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product)
            )
        )
        cart = cart_result.scalar_one()

        # Calculate totals
        cart_total = sum(
            float(item.price_snapshot) * item.quantity
            for item in cart.items
        )

        # Build cart items HTML
        cart_items_html = ""
        for cart_item in cart.items:
            item_total = float(cart_item.price_snapshot) * cart_item.quantity
            cart_items_html += f"""
            <tr data-item-id="{cart_item.id}">
                <td>
                    <div>
                        <strong>{cart_item.product.name}</strong><br>
                        <small class="text-muted">SKU: {cart_item.product.sku}</small>
                    </div>
                </td>
                <td class="text-center">
                    <input type="number" value="{cart_item.quantity}" min="1" max="999"
                           class="form-control form-control-sm text-center item-quantity"
                           style="width: 70px;" data-item-id="{cart_item.id}">
                </td>
                <td class="text-end">
                    {int(cart_item.price_snapshot)} MDLL<br>
                    <small class="text-muted">{cart_item.price_type}</small>
                </td>
                <td class="text-end">
                    <strong class="item-subtotal">{int(item_total)} MDL</strong>
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-sm btn-outline-danger"
                            onclick="removeItem({cart_item.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
            """

        return JSONResponse({
            "success": True,
            "product_name": product.name,
            "quantity": item.quantity,
            "cart_total": cart_total,
            "items_count": len(cart.items),
            "cart_items_html": cart_items_html
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@cart_router.post("/remove-item-ajax")
async def remove_cart_item_ajax(
        item_id: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge un item din coș (AJAX)."""
    try:
        # Get item with cart
        item_result = await db.execute(
            select(CartItem).where(CartItem.id == item_id)
        )
        item = item_result.scalar_one_or_none()

        if not item:
            return JSONResponse(
                status_code=404,
                content={"error": "Item negăsit"}
            )

        cart_id = item.cart_id

        # Delete item
        await db.delete(item)
        await db.commit()

        # Get updated cart
        cart_result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product)
            )
        )
        cart = cart_result.scalar_one_or_none()


        if not cart or not cart.items:
            # If cart empty, delete
            if cart:
                await db.delete(cart)
                await db.commit()
            return JSONResponse({
                "success": True,
                "cart_deleted": True,
                "message": "Coșul nu are produse. Va fi șters.",
                "redirect_url": "/dashboard/staff/cart"
            })

        # Calculate new total
        cart_total = sum(
            float(i.price_snapshot) * i.quantity
            for i in cart.items
        )

        # Render cart items HTML using the Jinja2 string template
        cart_items_html = j_template.render(cart=cart)

        return JSONResponse({
            "success": True,
            "cart_total": cart_total,
            "items_count": len(cart.items),
            "cart_items_html": cart_items_html,
            "cart_deleted": False
        })

    except Exception as e:
        print(f"Error removing cart item: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@cart_router.post("/update-item-ajax")
async def update_cart_item_ajax(
        item_id: int = Form(...),
        quantity: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează cantitate item (AJAX)."""

    try:
        # Update quantity
        await CartService.update_quantity(db, item_id, quantity)

        # Get updated cart info
        item_result = await db.execute(
            select(CartItem).where(CartItem.id == item_id)
        )
        item = item_result.scalar_one()

        cart_result = await db.execute(
            select(Cart)
            .where(Cart.id == item.cart_id)
            .options(selectinload(Cart.items))
        )
        cart = cart_result.scalar_one()

        # Calculate new totals
        item_subtotal = float(item.price_snapshot) * item.quantity
        cart_total = sum(
            float(i.price_snapshot) * i.quantity
            for i in cart.items
        )

        return JSONResponse({
            "success": True,
            "item_subtotal": item_subtotal,
            "cart_total": cart_total,
            "items_count": len(cart.items)
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@cart_router.post("/cleanup-empty-carts")
async def cleanup_empty_carts(
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "cart")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge toate coșurile goale din sistem."""
    try:
        # Găsește toate coșurile care nu au items
        subquery = select(CartItem.cart_id).distinct()
        empty_carts_query = select(Cart).where(~Cart.id.in_(subquery))

        result = await db.execute(empty_carts_query)
        empty_carts = result.scalars().all()

        count = len(empty_carts)

        # Șterge coșurile goale
        for cart in empty_carts:
            await db.delete(cart)

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/cart?success=cleaned&count={count}",
            status_code=303
        )
    except Exception as e:
        print(f"Error cleaning up empty carts: {e}")
        await db.rollback()
        return RedirectResponse(
            url="/dashboard/staff/cart?error=cleanup_failed",
            status_code=303
        )
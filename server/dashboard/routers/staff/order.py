# server/dashboard/routers/order.py
"""
Router pentru gestionarea comenzilor.
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Order, OrderStatus, Client, Product, Staff, Cart, CartItem
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.order_service import OrderService
from services.models.cart_service import CartService

order_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@order_router.get("/", response_class=HTMLResponse)
async def order_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        status: Optional[str] = None,
        search: Optional[str] = None,
        period: Optional[str] = None,
        client_id: Optional[int] = Query(None),
        sort_by: str = Query("created_at"),
        sort_desc: bool = Query(True),
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă comenzi cu filtre și paginare."""

    # Query de bază
    query = select(Order).options(
        selectinload(Order.client),
        selectinload(Order.items),
        selectinload(Order.processed_by)
    )

    # Filtre
    filters = []

    if status:
        filters.append(Order.status == OrderStatus(status))

    if client_id:
        filters.append(Order.client_id == client_id)

    if search:
        query = query.join(Client).where(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%")
            )
        )

    if period:
        now = datetime.utcnow()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None

        if start_date:
            filters.append(Order.created_at >= start_date)

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count(Order.id))
    if search:
        total_query = total_query.select_from(Order).join(Client).where(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%")
            )
        )
    if filters:
        total_query = total_query.where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare
    if sort_by == "order_number":
        order_by = Order.order_number
    elif sort_by == "total_amount":
        order_by = Order.total_amount
    elif sort_by == "status":
        order_by = Order.status
    else:
        order_by = Order.created_at

    if sort_desc:
        order_by = order_by.desc()

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(order_by).offset(offset).limit(per_page)

    result = await db.execute(query)
    orders = result.scalars().all()

    # Obține informații client dacă se filtrează după client
    filtered_client = None
    if client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        filtered_client = client_result.scalar_one_or_none()

    # Statistics
    if client_id:
        # Statistici specifice clientului
        total_orders = await db.execute(
            select(func.count(Order.id)).where(Order.client_id == client_id)
        )
        new_orders = await db.execute(
            select(func.count(Order.id)).where(
                and_(Order.client_id == client_id, Order.status == OrderStatus.NEW)
            )
        )
        processing_orders = await db.execute(
            select(func.count(Order.id)).where(
                and_(Order.client_id == client_id, Order.status == OrderStatus.PROCESSING)
            )
        )
        # Total venituri de la acest client
        client_revenue = await db.execute(
            select(func.sum(Order.total_amount)).where(
                and_(
                    Order.client_id == client_id,
                    Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED])
                )
            )
        )
    else:
        # Statistici globale
        total_orders = await db.execute(select(func.count(Order.id)))
        new_orders = await db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.NEW)
        )
        processing_orders = await db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.PROCESSING)
        )
        # Monthly revenue
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        client_revenue = await db.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.created_at >= month_start,
                    Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED])
                )
            )
        )

    stats = {
        "total_orders": total_orders.scalar() or 0,
        "new_orders": new_orders.scalar() or 0,
        "processing_orders": processing_orders.scalar() or 0,
        "monthly_revenue": float(client_revenue.scalar() or 0)
    }

    total_pages = (total + per_page - 1) // per_page

    # Logică navigare pentru întoarcerea la client
    back_url = None
    back_text = None
    page_title = "Comenzi"

    if filtered_client:
        back_url = f"/dashboard/staff/client/{client_id}"
        back_text = f"Înapoi la {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"
        page_title = f"Comenzi - {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"

    context = await get_template_context(request, staff)
    context.update({
        "page_title": page_title,
        "orders": orders,
        "stats": stats,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "search_query": search,
        "status_filter": status,
        "period_filter": period,
        "client_filter": client_id,
        "filtered_client": filtered_client,
        "back_url": back_url,
        "back_text": back_text,
        "sort_by": sort_by,
        "sort_desc": sort_desc,
        "order_statuses": [(s.value, s.value.title()) for s in OrderStatus]
    })

    return templates.TemplateResponse("order/list.html", context)


@order_router.get("/create", response_class=HTMLResponse)
async def order_create_form(
        request: Request,
        client_id: Optional[int] = Query(None),
        mode: Optional[str] = Query(None),  # 'manual' sau 'cart'
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Formular pentru creare comandă - selectare mod și client."""

    # Get client if specified
    client = None
    if client_id:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

    # Get all clients for selection
    clients_result = await db.execute(
        select(Client)
        .where(Client.is_active == True)
        .order_by(Client.first_name, Client.last_name)
    )
    clients = clients_result.scalars().all()

    # Dacă avem client și mod selectat, redirecționează direct
    if client_id and mode:
        if mode == 'cart':
            return RedirectResponse(
                url=f"/dashboard/staff/order/create-cart-order?client_id={client_id}",
                status_code=303
            )
        elif mode == 'manual':
            return RedirectResponse(
                url=f"/dashboard/staff/order/create-manual?client_id={client_id}",
                status_code=303
            )

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Comandă Nouă",
        "client": client,
        "clients": clients,
        "selected_mode": mode
    })

    return templates.TemplateResponse("order/create.html", context)


@order_router.post("/create-cart")
async def create_cart_for_order(
        client_id: int = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Creează coș nou pentru client și redirecționează la adăugare produse."""

    try:
        # Creează coș nou pentru client
        cart = await CartService.get_or_create_cart(
            db=db,
            client_id=client_id,
            session_id=f"dashboard-{staff.id}-{datetime.utcnow().timestamp()}"
        )

        # Redirecționează la pagina de adăugare produse
        return RedirectResponse(
            url=f"/dashboard/staff/order/add-products/{cart.id}",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating cart: {e}")
        return RedirectResponse(
            url="/dashboard/staff/order/create?error=create_failed",
            status_code=303
        )


@order_router.get("/create-manual", response_class=HTMLResponse)
async def create_manual_order_form(
        request: Request,
        client_id: int = Query(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Formular pentru creare comandă manuală directă."""

    # Get client
    client_result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = client_result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client negăsit")

    # Get products
    products_result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.prices),
            selectinload(Product.images)
        )
        .where(
            and_(
                Product.is_active == True,
                Product.in_stock == True
            )
        )
        .limit(100)
    )
    products = products_result.scalars().all()

    # Get categories
    from models import Category
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Comandă Manuală - {client.first_name or 'Client'} {client.last_name or ''}",
        "client": client,
        "products": products,
        "categories": categories
    })

    return templates.TemplateResponse("order/create_manual.html", context)


@order_router.post("/create-manual")
async def create_manual_order(
        request: Request,
        client_id: int = Form(...),
        client_note: Optional[str] = Form(None),
        products_data: str = Form(...),  # JSON cu produse și cantități
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Creează comandă manuală direct, fără coș."""

    try:
        import json

        # Log pentru debugging
        print(f"Creating manual order for client {client_id}")
        print(f"Products data: {products_data}")

        products = json.loads(products_data)

        if not products:
            raise ValueError("Nu ați selectat niciun produs")

        # Creează comanda direct
        order = await OrderService.create_manual_order(
            db=db,
            client_id=client_id,
            items=products,
            staff_id=staff.id,
            client_note=client_note
        )

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order.id}?success=created",
            status_code=303
        )

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/order/create-manual?client_id={client_id}&error=invalid_data",
            status_code=303
        )
    except Exception as e:
        print(f"Error creating manual order: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"/dashboard/staff/order/create-manual?client_id={client_id}&error=create_failed",
            status_code=303
        )


@order_router.get("/{order_id}", response_class=HTMLResponse)
async def order_detail(
        request: Request,
        order_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii comandă cu toate informațiile."""

    order = await OrderService.get_by_id(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Comandă negăsită")

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Comandă #{order.order_number}",
        "order": order
    })

    return templates.TemplateResponse("order/detail.html", context)


@order_router.post("/{order_id}/process")
async def process_order(
        order_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Marchează comanda ca în procesare."""

    try:
        order = await OrderService.update_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.PROCESSING,
            staff_id=staff.id
        )

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?success=updated",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=update_failed",
            status_code=303
        )


@order_router.post("/{order_id}/complete")
async def complete_order(
        order_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Marchează comanda ca finalizată."""

    try:
        order = await OrderService.update_status(
            db=db,
            order_id=order_id,
            new_status=OrderStatus.COMPLETED,
            staff_id=staff.id
        )

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?success=updated",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=update_failed",
            status_code=303
        )


@order_router.post("/{order_id}/cancel")
async def cancel_order(
        order_id: int,
        reason: str = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Anulează comanda."""

    try:
        order = await OrderService.cancel_order(
            db=db,
            order_id=order_id,
            reason=reason,
            cancelled_by=staff.id
        )

        return RedirectResponse(
            url="/dashboard/staff/order?success=order_cancelled",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=cancel_failed",
            status_code=303
        )


@order_router.post("/{order_id}/add-note")
async def add_staff_note(
        order_id: int,
        staff_note: str = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Adaugă notă staff la comandă."""

    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404)

        order.staff_note = staff_note
        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?success=note_added",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=note_failed",
            status_code=303
        )


@order_router.post("/{order_id}/generate-invoice")
async def generate_invoice(
        order_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Generează factură pentru comandă."""

    try:
        invoice = await OrderService.generate_invoice(db, order_id)

        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice.id}",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=invoice_failed",
            status_code=303
        )


@order_router.get("/add-products/{cart_id}", response_class=HTMLResponse)
async def add_products_to_cart(
        request: Request,
        cart_id: int,
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Pagină pentru adăugare produse în coș."""

    # Get cart with client
    cart_result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            selectinload(Cart.client),
            selectinload(Cart.items).selectinload(CartItem.product)
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
    from models import Category
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    # Calculate cart total
    cart_total = sum(
        float(item.price_snapshot) * item.quantity
        for item in cart.items
    )

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Adaugă Produse - {cart.client.first_name or 'Client'} {cart.client.last_name or ''}",
        "cart": cart,
        "cart_total": cart_total,
        "products": products,
        "categories": categories,
        "category_filter": category_id,
        "search_query": search
    })

    return templates.TemplateResponse("order/add_products.html", context)


@order_router.post("/add-product-to-cart")
async def add_product_to_cart(
        cart_id: int = Form(...),
        product_id: int = Form(...),
        quantity: int = Form(1),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
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

        # Get product details for response
        product_result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one()

        # Get updated cart with all items
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
            <div class="cart-item d-flex justify-content-between align-items-start mb-2 pb-2 border-bottom" data-item-id="{cart_item.id}">
                <div class="flex-grow-1">
                    <small class="d-block fw-bold">{cart_item.product.name}</small>
                    <small class="text-muted">
                        {cart_item.quantity} x {int(cart_item.price_snapshot)} MDL
                    </small>
                </div>
                <div class="text-end">
                    <strong>{int(item_total)} MDL</strong>
                    <button type="button" class="btn btn-sm btn-link text-danger p-0 ms-2" 
                            onclick="removeFromCart({cart_item.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            """

        return JSONResponse({
            "success": True,
            "product_name": product.name,
            "quantity": item.quantity,
            "cart_total": cart_total,
            "items_count": len(cart.items),
            "cart_items_html": cart_items_html,
            "item_id": item.id
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@order_router.delete("/remove-cart-item/{item_id}")
async def remove_cart_item_ajax(
        item_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge item din coș (AJAX)."""

    try:
        # Get item to find cart_id
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

        # Remove item
        await CartService.update_quantity(db, item_id, 0)

        # Get updated cart
        cart_result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items))
        )
        cart = cart_result.scalar_one()

        # Calculate new total
        cart_total = sum(
            float(item.price_snapshot) * item.quantity
            for item in cart.items
        )

        return JSONResponse({
            "success": True,
            "cart_total": cart_total,
            "items_count": len(cart.items)
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@order_router.post("/finalize/{cart_id}")
async def finalize_order(
        cart_id: int,
        client_note: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Finalizează și creează comanda din coș."""

    try:
        # Create order from cart
        order = await OrderService.create_from_cart(
            db=db,
            cart_id=cart_id,
            client_note=client_note
        )

        # Mark as processing since it's created by staff
        order.status = OrderStatus.PROCESSING
        order.processed_by_id = staff.id
        order.processed_at = datetime.utcnow()
        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order.id}?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating order: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/order/add-products/{cart_id}?error=create_failed",
            status_code=303
        )


# API endpoints pentru comandă manuală
@order_router.get("/api/products/search")
async def search_products_api(
        q: str = Query(""),
        category_id: Optional[int] = None,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """API pentru căutare produse (folosit în comandă manuală)."""

    query = select(Product).options(
        selectinload(Product.prices),
        selectinload(Product.category)
    ).where(
        and_(
            Product.is_active == True,
            Product.in_stock == True
        )
    )

    if q:
        query = query.where(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.sku.ilike(f"%{q}%")
            )
        )

    if category_id:
        query = query.where(Product.category_id == category_id)

    query = query.limit(20)

    result = await db.execute(query)
    products = result.scalars().all()

    # Format pentru răspuns JSON
    products_data = []
    for product in products:
        # Găsește prețul pentru statusul clientului
        price = None
        for p in product.prices:
            if p.is_active:
                price = float(p.amount)
                break

        products_data.append({
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "category": product.category.name if product.category else "",
            "price": price or 0,
            "in_stock": product.in_stock
        })

    return JSONResponse(content=products_data)




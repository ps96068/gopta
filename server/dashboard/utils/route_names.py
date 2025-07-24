# server/dashboard/utils/route_names.py
"""
Registry centralizat pentru TOATE rutele din Staff Dashboard.
Actualizat cu lista completă de routere existente.

Acest registry permite:
1. Template-urilor să folosească url_for() fără erori
2. Dezvoltare incrementală - rutele lipsă returnează URL dummy
3. Documentare centralizată a tuturor rutelor
4. Verificare ușoară a rutelor implementate vs planificate
"""


from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class RouteModule(str, Enum):
    """Module care conțin rute în dashboard."""
    # Core modules
    HOME = "home"
    AUTH = "auth"

    # Resource management
    PRODUCTS = "products"
    PRODUCT_IMAGE = "product_image"
    PRODUCT_PRICE = "product_price"
    CATEGORY = "category"

    # User management
    CLIENTS = "clients"
    STAFF = "staff"
    VENDOR_COMPANY = "vendor_company"
    VENDOR_STAFF = "vendor_staff"

    # Sales & Commerce
    CART = "cart"
    ORDERS = "orders"
    INVOICE = "invoice"

    # Content & Marketing
    POST = "post"
    POST_IMAGE = "post_image"

    # Analytics & Support
    ANALYTICS = "analytics"
    USER_REQUEST = "user_request"


@dataclass
class RouteInfo:
    """Informații despre o rută."""
    name: str
    module: RouteModule
    path_template: str
    description: str
    implemented: bool = True  # Flag pentru a marca rutele neimplementate


class RouteRegistry:
    """
    Registry pentru nume de rute folosite în dashboard.
    Centralizează toate numele de rute pentru a evita hard-coding în template-uri.
    """

    # Dicționar cu TOATE rutele cunoscute din dashboard
    _routes: Dict[str, RouteInfo] = {

        # ==================== HOME & AUTH ====================
        "dashboard_home": RouteInfo(
            name="dashboard_home",
            module=RouteModule.HOME,
            path_template="/dashboard/staff/",
            description="Dashboard principal"
        ),
        "dashboard_stats": RouteInfo(
            name="dashboard_stats",
            module=RouteModule.HOME,
            path_template="/dashboard/staff/stats",
            description="Statistici detaliate"
        ),
        "dashboard_activity": RouteInfo(
            name="dashboard_activity",
            module=RouteModule.HOME,
            path_template="/dashboard/staff/activity",
            description="Activitate recentă"
        ),

        # ==================== PRODUCTS ====================
        "product_list": RouteInfo(
            name="product_list",
            module=RouteModule.PRODUCTS,
            path_template="/dashboard/staff/product",
            description="Listă produse"
        ),
        "product_create": RouteInfo(
            name="product_create",
            module=RouteModule.PRODUCTS,
            path_template="/dashboard/staff/product/create",
            description="Creare produs nou"
        ),
        "product_detail": RouteInfo(
            name="product_detail",
            module=RouteModule.PRODUCTS,
            path_template="/dashboard/staff/product/{product_id}",
            description="Detalii produs"
        ),
        "product_edit": RouteInfo(
            name="product_edit",
            module=RouteModule.PRODUCTS,
            path_template="/dashboard/staff/product/{product_id}/edit",
            description="Editare produs"
        ),

        # ==================== PRODUCT IMAGES ====================
        "product_image_gallery": RouteInfo(
            name="product_image_gallery",
            module=RouteModule.PRODUCT_IMAGE,
            path_template="/dashboard/staff/product_image/",
            description="Galerie imagini produse"
        ),
        "product_image_detail": RouteInfo(
            name="product_image_detail",
            module=RouteModule.PRODUCT_IMAGE,
            path_template="/dashboard/staff/product_image/product/{product_id}",
            description="Imagini produs specific"
        ),

        # ==================== PRODUCT PRICES ====================
        "price_list": RouteInfo(
            name="price_list",
            module=RouteModule.PRODUCT_PRICE,
            path_template="/dashboard/staff/product_price/",
            description="Listă prețuri produse"
        ),
        "product_price_detail": RouteInfo(
            name="product_price_detail",
            module=RouteModule.PRODUCT_PRICE,
            path_template="/dashboard/staff/product_price/product/{product_id}",
            description="Prețuri produs specific"
        ),

        # ==================== CATEGORIES ====================
        "category_list": RouteInfo(
            name="category_list",
            module=RouteModule.CATEGORY,
            path_template="/dashboard/staff/category",
            description="Listă categorii"
        ),
        "category_create": RouteInfo(
            name="category_create",
            module=RouteModule.CATEGORY,
            path_template="/dashboard/staff/category/create",
            description="Creare categorie nouă"
        ),
        "category_detail": RouteInfo(
            name="category_detail",
            module=RouteModule.CATEGORY,
            path_template="/dashboard/staff/category/{category_id}",
            description="Detalii categorie"
        ),
        "category_edit": RouteInfo(
            name="category_edit",
            module=RouteModule.CATEGORY,
            path_template="/dashboard/staff/category/{category_id}/edit",
            description="Editare categorie"
        ),

        # ==================== CLIENTS ====================
        "client_list": RouteInfo(
            name="client_list",
            module=RouteModule.CLIENTS,
            path_template="/dashboard/staff/client",
            description="Listă clienți"
        ),
        "client_create": RouteInfo(
            name="client_create",
            module=RouteModule.CLIENTS,
            path_template="/dashboard/staff/client/create",
            description="Creare client nou"
        ),
        "client_detail": RouteInfo(
            name="client_detail",
            module=RouteModule.CLIENTS,
            path_template="/dashboard/staff/client/{client_id}",
            description="Detalii client"
        ),
        "client_edit": RouteInfo(
            name="client_edit",
            module=RouteModule.CLIENTS,
            path_template="/dashboard/staff/client/{client_id}/edit",
            description="Editare client"
        ),

        # ==================== CART ====================
        "cart_list": RouteInfo(
            name="cart_list",
            module=RouteModule.CART,
            path_template="/dashboard/staff/cart",
            description="Listă coșuri"
        ),
        "cart_create": RouteInfo(
            name="cart_create",
            module=RouteModule.CART,
            path_template="/dashboard/staff/cart/create",
            description="Creare coș nou"
        ),
        "cart_detail": RouteInfo(
            name="cart_detail",
            module=RouteModule.CART,
            path_template="/dashboard/staff/cart/{cart_id}",
            description="Detalii coș"
        ),
        "manage_cart": RouteInfo(
            name="manage_cart",
            module=RouteModule.CART,
            path_template="/dashboard/staff/cart/manage/{cart_id}",
            description="Gestionare produse în coș"
        ),

        # ==================== ORDERS ====================
        "order_list": RouteInfo(
            name="order_list",
            module=RouteModule.ORDERS,
            path_template="/dashboard/staff/order",
            description="Listă comenzi"
        ),
        "order_create": RouteInfo(
            name="order_create",
            module=RouteModule.ORDERS,
            path_template="/dashboard/staff/order/create",
            description="Creare comandă nouă"
        ),
        "order_detail": RouteInfo(
            name="order_detail",
            module=RouteModule.ORDERS,
            path_template="/dashboard/staff/order/{order_id}",
            description="Detalii comandă"
        ),

        # ==================== INVOICE ====================
        "invoice_list": RouteInfo(
            name="invoice_list",
            module=RouteModule.INVOICE,
            path_template="/dashboard/staff/invoice",
            description="Listă facturi și oferte"
        ),
        "invoice_detail": RouteInfo(
            name="invoice_detail",
            module=RouteModule.INVOICE,
            path_template="/dashboard/staff/invoice/{invoice_id}",
            description="Detalii factură/ofertă"
        ),
        "download_invoice": RouteInfo(
            name="download_invoice",
            module=RouteModule.INVOICE,
            path_template="/dashboard/staff/invoice/{invoice_id}/download",
            description="Descărcare PDF"
        ),

        # ==================== ANALYTICS ====================
        "analytics_overview": RouteInfo(
            name="analytics_overview",
            module=RouteModule.ANALYTICS,
            path_template="/dashboard/staff/analytics/",
            description="Analytics Overview"
        ),
        "analytics_products": RouteInfo(
            name="analytics_products",
            module=RouteModule.ANALYTICS,
            path_template="/dashboard/staff/analytics/products",
            description="Analiză produse"
        ),
        "analytics_users": RouteInfo(
            name="analytics_users",
            module=RouteModule.ANALYTICS,
            path_template="/dashboard/staff/analytics/users",
            description="Analiză utilizatori"
        ),
        "user_journey": RouteInfo(
            name="user_journey",
            module=RouteModule.ANALYTICS,
            path_template="/dashboard/staff/analytics/user/{client_id}/journey",
            description="User journey"
        ),
        "export_analytics": RouteInfo(
            name="export_analytics",
            module=RouteModule.ANALYTICS,
            path_template="/dashboard/staff/analytics/export",
            description="Export analytics"
        ),

        # ==================== USER REQUESTS ====================
        "user_request_list": RouteInfo(
            name="user_request_list",
            module=RouteModule.USER_REQUEST,
            path_template="/dashboard/staff/user_request",
            description="Listă cereri utilizatori"
        ),
        "user_request_detail": RouteInfo(
            name="user_request_detail",
            module=RouteModule.USER_REQUEST,
            path_template="/dashboard/staff/user_request/{request_id}",
            description="Detalii cerere"
        ),

        # ==================== BLOG POSTS ====================
        "post_list": RouteInfo(
            name="post_list",
            module=RouteModule.POST,
            path_template="/dashboard/staff/post",
            description="Listă articole blog"
        ),
        "post_create": RouteInfo(
            name="post_create",
            module=RouteModule.POST,
            path_template="/dashboard/staff/post/create",
            description="Creare articol nou"
        ),
        "post_detail": RouteInfo(
            name="post_detail",
            module=RouteModule.POST,
            path_template="/dashboard/staff/post/{post_id}",
            description="Detalii articol",
            implemented=False  # Marchează ca neimplementat dacă nu există
        ),
        "post_edit": RouteInfo(
            name="post_edit",
            module=RouteModule.POST,
            path_template="/dashboard/staff/post/{post_id}/edit",
            description="Editare articol"
        ),
        "post_preview": RouteInfo(
            name="post_preview",
            module=RouteModule.POST,
            path_template="/dashboard/staff/post/{post_id}/preview",
            description="Preview articol"
        ),

        # ==================== POST IMAGES ====================
        "post_images_gallery": RouteInfo(
            name="post_images_gallery",
            module=RouteModule.POST_IMAGE,
            path_template="/dashboard/staff/post_image/",
            description="Galerie imagini articole"
        ),
        "post_images_list": RouteInfo(
            name="post_images_list",
            module=RouteModule.POST_IMAGE,
            path_template="/dashboard/staff/post_image/{post_id}",
            description="Imagini articol specific"
        ),

        # ==================== STAFF ====================
        "staff_list": RouteInfo(
            name="staff_list",
            module=RouteModule.STAFF,
            path_template="/dashboard/staff/staff",
            description="Listă membri staff"
        ),
        "staff_create": RouteInfo(
            name="staff_create",
            module=RouteModule.STAFF,
            path_template="/dashboard/staff/staff/create",
            description="Creare staff nou"
        ),
        "staff_detail": RouteInfo(
            name="staff_detail",
            module=RouteModule.STAFF,
            path_template="/dashboard/staff/staff/{staff_id}",
            description="Detalii membru staff"
        ),
        "staff_edit": RouteInfo(
            name="staff_edit",
            module=RouteModule.STAFF,
            path_template="/dashboard/staff/staff/{staff_id}/edit",
            description="Editare staff"
        ),
        "staff_permissions": RouteInfo(
            name="staff_permissions",
            module=RouteModule.STAFF,
            path_template="/dashboard/staff/staff/{staff_id}/permissions",
            description="Permisiuni staff"
        ),

        # ==================== VENDOR COMPANY ====================
        "list_companies": RouteInfo(
            name="list_companies",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/",
            description="Listă companii vendor"
        ),
        "create_company": RouteInfo(
            name="create_company",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/create",
            description="Creare companie nouă"
        ),
        "view_company": RouteInfo(
            name="view_company",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/{company_id}",
            description="Detalii companie"
        ),
        "edit_company": RouteInfo(
            name="edit_company",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/{company_id}/edit",
            description="Editare companie"
        ),
        "company_products": RouteInfo(
            name="company_products",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/{company_id}/products",
            description="Produse companie"
        ),
        "company_staff": RouteInfo(
            name="company_staff",
            module=RouteModule.VENDOR_COMPANY,
            path_template="/dashboard/staff/vendor_company/{company_id}/staff",
            description="Angajați companie"
        ),

        # ==================== VENDOR STAFF ====================
        "list_vendor_staff": RouteInfo(
            name="list_vendor_staff",
            module=RouteModule.VENDOR_STAFF,
            path_template="/dashboard/staff/vendor_staff/",
            description="Listă angajați vendor"
        ),
        "create_vendor_staff": RouteInfo(
            name="create_vendor_staff",
            module=RouteModule.VENDOR_STAFF,
            path_template="/dashboard/staff/vendor_staff/create",
            description="Creare angajat vendor"
        ),
        "view_vendor_staff": RouteInfo(
            name="view_vendor_staff",
            module=RouteModule.VENDOR_STAFF,
            path_template="/dashboard/staff/vendor_staff/{staff_id}",
            description="Detalii angajat vendor"
        ),
        "edit_vendor_staff": RouteInfo(
            name="edit_vendor_staff",
            module=RouteModule.VENDOR_STAFF,
            path_template="/dashboard/staff/vendor_staff/{staff_id}/edit",
            description="Editare angajat vendor"
        ),
    }

    @classmethod
    def get_route_info(cls, name: str) -> Optional[RouteInfo]:
        """Obține informații despre o rută."""
        return cls._routes.get(name)

    @classmethod
    def get_routes_by_module(cls, module: RouteModule) -> Dict[str, RouteInfo]:
        """Obține toate rutele dintr-un modul."""
        return {
            name: info
            for name, info in cls._routes.items()
            if info.module == module
        }

    @classmethod
    def register_route(cls, name: str, info: RouteInfo):
        """Înregistrează o rută nouă (pentru extensibilitate)."""
        cls._routes[name] = info

    @classmethod
    def get_all_routes(cls) -> Dict[str, RouteInfo]:
        """Obține toate rutele înregistrate."""
        return cls._routes.copy()

    @classmethod
    def get_unimplemented_routes(cls) -> List[RouteInfo]:
        """Returnează lista rutelor care nu sunt încă implementate."""
        return [info for info in cls._routes.values() if not info.implemented]

    @classmethod
    def validate_route_name(cls, name: str) -> bool:
        """Verifică dacă un nume de rută există în registry."""
        return name in cls._routes


# Funcții helper pentru template-uri
def generate_dummy_url(route_name: str, **params) -> str:
    """
    Generează URL dummy pentru rute care nu sunt încă implementate.
    Folosit ca fallback în template-uri.
    """
    route_info = RouteRegistry.get_route_info(route_name)
    if route_info:
        url = route_info.path_template
        # Înlocuiește parametrii din template
        for key, value in params.items():
            # Suportă atât {param} cât și {param:type}
            url = url.replace(f"{{{key}}}", str(value))
            url = url.replace(f"{{{key}:int}}", str(value))
            url = url.replace(f"{{{key}:str}}", str(value))
        return url
    return f"#route-not-found-{route_name}"


def get_dashboard_url_for(request, route_name: str, **params) -> str:
    """
    Wrapper pentru url_for care gestionează rute lipsă.
    Returnează URL real dacă ruta există, altfel URL dummy.

    Utilizare în template:
    {{ url_for('product_detail', product_id=123) }}
    """
    if not request:
        # Dacă nu avem request, returnăm URL dummy
        return generate_dummy_url(route_name, **params)

    try:
        # Încearcă să obțină URL-ul real folosind request.url_for
        return request.url_for(route_name, **params)
    except Exception as e:
        # Debug în development
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Route '{route_name}' not found in app, using dummy URL. Error: {e}")

        # Dacă ruta nu există, returnează URL dummy
        return generate_dummy_url(route_name, **params)


# Funcții utilitare pentru development
def print_route_status():
    """Printează statusul tuturor rutelor pentru debugging."""
    print("\n=== ROUTE REGISTRY STATUS ===")

    by_module = {}
    for name, info in RouteRegistry._routes.items():
        if info.module not in by_module:
            by_module[info.module] = []
        by_module[info.module].append((name, info))

    for module, routes in sorted(by_module.items()):
        print(f"\n{module.value.upper()}:")
        for name, info in sorted(routes):
            status = "✓" if info.implemented else "✗"
            print(f"  {status} {name:30} - {info.description}")

    # Sumar
    total = len(RouteRegistry._routes)
    implemented = sum(1 for r in RouteRegistry._routes.values() if r.implemented)
    print(f"\nTOTAL: {implemented}/{total} rute implementate ({implemented / total * 100:.1f}%)")


def check_template_routes(template_content: str) -> List[str]:
    """
    Verifică ce rute sunt folosite într-un template.
    Util pentru debugging.
    """
    import re

    # Caută toate apelurile url_for
    pattern = r"url_for\s*\(\s*['\"]([^'\"]+)['\"]"
    found_routes = re.findall(pattern, template_content)

    missing_routes = []
    for route in found_routes:
        if not RouteRegistry.validate_route_name(route):
            missing_routes.append(route)

    return missing_routes
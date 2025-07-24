# server/dashboard/config.py
"""
Configurări pentru Dashboard Module.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

#
# class DashboardConfig(BaseModel):
#     """Configurări principale pentru dashboard."""
#
#     # Routing
#     base_route: str = Field(default="/dashboard", description="Base URL pentru dashboard")
#     title: str = Field(default="PCE Admin Dashboard", description="Titlu dashboard")
#
#     # Authentication
#     login_url: str = Field(default="/dashboard/auth/login", description="URL login")
#     session_expire_minutes: int = Field(default=480, description="8 ore")
#
#     # Permissions
#     enable_role_based_access: bool = True
#     roles_hierarchy: Dict[str, int] = {
#         "super_admin": 100,
#         "manager": 50,
#         "supervisor": 10
#     }
#
#     # Features
#     enable_import: bool = True
#     enable_export: bool = True
#     enable_file_upload: bool = True
#     enable_bulk_actions: bool = True
#     enable_global_search: bool = True
#
#     # File Upload
#     upload_max_size_mb: int = 2
#     upload_allowed_extensions: List[str] = [".png", ".jpg", ".jpeg"]
#
#     # Import/Export
#     import_allowed_formats: List[str] = [".csv", ".xls", ".xlsx"]
#     import_max_rows: int = 10000
#     export_max_rows: int = 50000
#
#     # UI Settings
#     items_per_page: int = 20
#     max_items_per_page: int = 100
#     enable_dark_mode: bool = False
#     default_language: str = "ro"
#
#     # Paths (relative to project root)
#     static_path: str = "static/webapp"
#     templates_path: str = "dashboard/templates"
#
#     # Image storage paths
#     image_paths: Dict[str, str] = {
#         "blog": "static/webapp/img/blog",
#         "category": "static/webapp/img/category",
#         "product": "static/webapp/img/product",
#         "invoice": "static/webapp/img/invoice"
#     }
#
#     # Statistics refresh
#     stats_cache_minutes: int = 5
#
#     # Activity tracking
#     track_user_activity: bool = True
#     activity_retention_days: int = 30
#
#
#     # Feature flags pentru dezvoltare graduală
#     enable_vendor_dashboard: bool = Field(
#         default=False,
#         description="Activează dashboard pentru vendori"
#     )
#     enable_multi_vendor: bool = Field(
#         default=False,
#         description="Permite mai mulți vendori (post-MVP)"
#     )


# Default config instance


class DashboardConfig(BaseModel):
    """Configurări principale pentru dashboard."""

    # Routing
    base_route: str = Field(default="/dashboard", description="Base URL pentru dashboard")
    title: str = Field(default="PCE Dashboard", description="Titlu dashboard")

    # Authentication
    login_url: str = Field(default="/dashboard/auth/login", description="URL login")
    session_expire_minutes: int = Field(default=480, description="8 ore")

    # Permissions
    enable_role_based_access: bool = True


    # Feature flags
    enable_vendor_dashboard: bool = Field(
        default=True,
        description="Activează dashboard pentru vendori"
    )

    roles_hierarchy: Dict[str, int] = {
        "super_admin": 100,
        "manager": 50,
        "supervisor": 10,
        "vendor_admin": 40,
        "vendor_manager": 20
    }

    # Features
    enable_import: bool = True
    enable_export: bool = True
    enable_file_upload: bool = True
    enable_bulk_actions: bool = True
    enable_global_search: bool = True
    enable_vendor_dashboard: bool = True  # Activat pentru vendor

    # File Upload
    upload_max_size_mb: int = 2
    upload_allowed_extensions: List[str] = [".png", ".jpg", ".jpeg"]

    # Import/Export
    import_allowed_formats: List[str] = [".csv", ".xls", ".xlsx"]
    import_max_rows: int = 10000
    export_max_rows: int = 50000

    # UI Settings
    items_per_page: int = 20
    max_items_per_page: int = 100
    enable_dark_mode: bool = False
    default_language: str = "ro"

    # Paths (relative to project root)
    static_path: str = "static/webapp"
    templates_path: str = "dashboard/templates"

    # Image storage paths
    image_paths: Dict[str, str] = {
        "blog": "static/webapp/img/blog",
        "category": "static/webapp/img/category",
        "product": "static/webapp/img/product",
        "invoice": "static/webapp/img/invoice",
        "vendor": "static/webapp/img/vendor"
    }

    # Statistics refresh
    stats_cache_minutes: int = 5

    # Activity tracking
    track_user_activity: bool = True
    activity_retention_days: int = 30


# Default config instance
default_config = DashboardConfig()

#
# class ModelConfig(BaseModel):
#     """Configurare pentru un model specific în dashboard."""
#
#     name: str
#     display_name: str
#     icon: str = "bi-box"  # Bootstrap icon
#
#     # Permissions
#     allow_create: bool = True
#     allow_read: bool = True
#     allow_update: bool = True
#     allow_delete: bool = True
#     allow_import: bool = False
#     allow_export: bool = True
#
#     # Features
#     enable_search: bool = True
#     enable_filters: bool = True
#     enable_bulk_actions: bool = True
#
#     # Fields to display in list view
#     list_fields: List[str]
#     # Fields to display in detail view
#     detail_fields: Optional[List[str]] = None
#     # Fields that are searchable
#     search_fields: List[str]
#     # Fields that can be filtered
#     filter_fields: List[str]
#
#     # Custom actions
#     custom_actions: List[Dict[str, str]] = Field(default_factory=list)
#
#     # Validation rules
#     required_fields: List[str]
#     unique_fields: List[str] = Field(default_factory=list)




# Model configurations



class ModelConfig(BaseModel):
    """Configurare pentru un model specific în dashboard."""

    name: str
    display_name: str
    icon: str = "bi-box"

    # Permissions
    allow_create: bool = True
    allow_read: bool = True
    allow_update: bool = True
    allow_delete: bool = True
    allow_import: bool = False
    allow_export: bool = True

    # Features
    enable_search: bool = True
    enable_filters: bool = True
    enable_bulk_actions: bool = True

    # Fields to display
    list_fields: List[str]
    detail_fields: Optional[List[str]] = None
    search_fields: List[str]
    filter_fields: List[str]

    # Custom actions
    custom_actions: List[Dict[str, str]] = Field(default_factory=list)

    # Validation rules
    required_fields: List[str]
    unique_fields: List[str] = Field(default_factory=list)




# Functions to get config based on user type

STAFF_MODELS_CONFIG = {
    # UTILIZATORI
    "client": ModelConfig(
        name="client",
        display_name="Clienți",
        icon="bi-people",
        list_fields=["id", "telegram_id", "status", "first_name", "last_name", "phone", "created_at"],
        search_fields=["first_name", "last_name", "email", "phone", "telegram_id"],
        filter_fields=["status", "created_at"],
        required_fields=["telegram_id"],
        allow_import=True,
        allow_export=True
    ),

    "vendor_company": ModelConfig(
        name="vendor_company",
        display_name="Companii Vendor",
        icon="bi-building",
        list_fields=["id", "name", "legal_name", "tax_id", "email", "is_verified", "is_active"],
        search_fields=["name", "legal_name", "email", "tax_id"],
        filter_fields=["is_verified", "is_active"],
        required_fields=["name", "legal_name", "tax_id", "email", "phone", "address"],
        unique_fields=["tax_id", "name"],
        allow_import=False,
        custom_actions=[
            {"name": "verify", "label": "Verifică", "icon": "bi-check-circle"},
            {"name": "toggle_active", "label": "Activează/Dezactivează", "icon": "bi-toggle-on"}
        ]
    ),

    "vendor_staff": ModelConfig(
        name="vendor_staff",
        display_name="Personal Vendor",
        icon="bi-person-badge",
        list_fields=["id", "company_id", "email", "first_name", "last_name", "role", "is_active"],
        search_fields=["email", "first_name", "last_name"],
        filter_fields=["company_id", "role", "is_active"],
        required_fields=["email", "password", "first_name", "last_name", "company_id", "role"],
        unique_fields=["email"],
        allow_import=False
    ),

    "staff": ModelConfig(
        name="staff",
        display_name="Staff PCE",
        icon="bi-person-workspace",
        list_fields=["id", "email", "first_name", "last_name", "role", "is_active", "last_login"],
        search_fields=["email", "first_name", "last_name"],
        filter_fields=["role", "is_active"],
        required_fields=["email", "password", "first_name", "last_name", "role"],
        unique_fields=["email"],
        allow_import=False,
        custom_actions=[
            {"name": "permissions", "label": "Permisiuni", "icon": "bi-shield-check"}
        ]
    ),

    # CATALOG
    "category": ModelConfig(
        name="category",
        display_name="Categorii",
        icon="bi-tags",
        list_fields=["id", "name", "slug", "parent_id", "sort_order", "is_active"],
        search_fields=["name", "slug", "description"],
        filter_fields=["parent_id", "is_active"],
        required_fields=["name", "slug"],
        unique_fields=["slug"],
        allow_import=True,
        allow_export=True
    ),

    "product": ModelConfig(
        name="product",
        display_name="Produse",
        icon="bi-box-seam",
        list_fields=["id", "sku", "name", "category_id", "vendor_company_id", "is_active", "in_stock"],
        search_fields=["name", "sku", "description"],
        filter_fields=["category_id", "vendor_company_id", "is_active", "in_stock"],
        required_fields=["name", "sku", "category_id", "vendor_company_id"],
        unique_fields=["sku", "slug"],
        allow_import=True,
        allow_export=True,
        custom_actions=[
            {"name": "manage_images", "label": "Imagini", "icon": "bi-images"},
            {"name": "manage_prices", "label": "Prețuri", "icon": "bi-currency-dollar"},
            {"name": "duplicate", "label": "Duplică", "icon": "bi-copy"}
        ]
    ),

    "product_image": ModelConfig(
        name="product_image",
        display_name="Imagini Produse",
        icon="bi-images",
        list_fields=["id", "product_id", "file_name", "is_primary", "sort_order"],
        search_fields=["file_name", "alt_text"],
        filter_fields=["product_id", "is_primary"],
        required_fields=["product_id", "image_path", "file_name"],
        allow_create=False,  # Se creează prin upload pe produs
        allow_import=False,
        allow_export=True
    ),

    "product_price": ModelConfig(
        name="product_price",
        display_name="Prețuri Produse",
        icon="bi-currency-dollar",
        list_fields=["id", "product_id", "price_type", "amount", "currency", "updated_at"],
        search_fields=["product_id"],
        filter_fields=["price_type", "currency"],
        required_fields=["product_id", "price_type", "amount"],
        allow_create=False,  # Se gestionează per produs
        allow_delete=False,  # Nu ștergem prețuri
        allow_import=True,
        allow_export=True,
        custom_actions=[
            {"name": "bulk_update", "label": "Actualizare în masă", "icon": "bi-pencil-square"}
        ]
    ),

    # VÂNZĂRI
    "cart": ModelConfig(
        name="cart",
        display_name="Coșuri",
        icon="bi-cart",
        list_fields=["id", "cart_number", "client_id", "total_amount", "created_at", "updated_at"],
        search_fields=["cart_number"],
        filter_fields=["created_at", "updated_at"],
        required_fields=["client_id"],
        allow_create=False,  # Se creează automat
        allow_import=False,
        custom_actions=[
            {"name": "convert_to_order", "label": "Transformă în Comandă", "icon": "bi-arrow-right-circle"},
            {"name": "generate_quote", "label": "Generează Ofertă", "icon": "bi-file-earmark-text"}
        ]
    ),

    "order": ModelConfig(
        name="order",
        display_name="Comenzi",
        icon="bi-cart-check",
        list_fields=["id", "order_number", "client_id", "status", "total_amount", "created_at"],
        search_fields=["order_number"],
        filter_fields=["status", "created_at", "client_id", "processed_by_id"],
        required_fields=["client_id"],
        allow_create=False,  # Se creează din coș
        allow_delete=False,  # Nu ștergem comenzi, doar anulăm
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "process", "label": "Procesează", "icon": "bi-check-circle"},
            {"name": "complete", "label": "Finalizează", "icon": "bi-check-all"},
            {"name": "cancel", "label": "Anulează", "icon": "bi-x-circle"},
            {"name": "generate_invoice", "label": "Generează Factură", "icon": "bi-receipt"}
        ]
    ),

    "invoice": ModelConfig(
        name="invoice",
        display_name="Facturi/Oferte",
        icon="bi-receipt",
        list_fields=["id", "invoice_number", "invoice_type", "client_name", "total_amount", "sent_at"],
        search_fields=["invoice_number", "client_name", "client_email"],
        filter_fields=["invoice_type", "sent_at", "converted_to_order"],
        required_fields=["invoice_type", "client_name", "client_email", "total_amount"],
        allow_create=False,  # Se generează automat
        allow_delete=False,
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "send", "label": "Trimite", "icon": "bi-send"},
            {"name": "download", "label": "Descarcă PDF", "icon": "bi-download"},
            {"name": "convert_to_order", "label": "Convertește în Comandă", "icon": "bi-arrow-right"}
        ]
    ),

    # Blog
    "post": ModelConfig(
        name="post",
        display_name="Articole Blog",
        icon="bi-newspaper",  # Icon mai potrivit pentru blog
        list_fields=["id", "title", "author_id", "is_featured", "is_active", "view_count", "created_at"],
        search_fields=["title", "content", "excerpt"],
        filter_fields=["author_id", "is_featured", "is_active"],
        required_fields=["title", "slug", "content", "author_id", "meta_title", "meta_description"],
        unique_fields=["slug"],  # slug trebuie să fie unic, nu title
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "preview", "label": "Preview", "icon": "bi-eye"},
            {"name": "toggle_featured", "label": "Featured On/Off", "icon": "bi-star"},
            {"name": "manage_images", "label": "Imagini", "icon": "bi-images"}
        ]
    ),

    "post_image": ModelConfig(
        name="post_image",
        display_name="Imagini Articole",
        icon="bi-images",
        list_fields=["id", "post_id", "file_name", "is_featured", "sort_order", "caption"],
        search_fields=["file_name", "alt_text", "caption"],
        filter_fields=["post_id", "is_featured"],
        required_fields=["post_id", "image_path", "file_name", "file_size"],
        allow_create=False,  # Se creează prin upload pe post
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "set_featured", "label": "Setează ca principală", "icon": "bi-star-fill"},
            {"name": "reorder", "label": "Reordonează", "icon": "bi-arrow-down-up"}
        ]
    ),

    # COMUNICARE
    "user_request": ModelConfig(
        name="user_request",
        display_name="Cereri Utilizatori",
        icon="bi-envelope",
        list_fields=["id", "client_id", "request_type", "product_id", "is_processed", "created_at"],
        search_fields=["message"],
        filter_fields=["request_type", "is_processed", "created_at"],
        required_fields=["client_id", "request_type", "message"],
        allow_create=False,  # Vin din WebApp/Bot
        allow_delete=False,
        allow_import=False,
        custom_actions=[
            {"name": "respond", "label": "Răspunde", "icon": "bi-reply"},
            {"name": "mark_processed", "label": "Marchează Procesat", "icon": "bi-check"}
        ]
    ),

    # CONTENT
    "post": ModelConfig(
        name="post",
        display_name="Articole Blog",
        icon="bi-newspaper",
        list_fields=["id", "title", "slug", "author_id", "is_featured", "is_active", "view_count"],
        search_fields=["title", "content", "excerpt"],
        filter_fields=["author_id", "is_featured", "is_active"],
        required_fields=["title", "slug", "content", "author_id"],
        unique_fields=["slug"],
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "preview", "label": "Preview", "icon": "bi-eye"},
            {"name": "toggle_featured", "label": "Featured On/Off", "icon": "bi-star"}
        ]
    )
}

STAFF_MENU_STRUCTURE = [
    {
        "header": "Principal",
        "items": [
            {
                "name": "dashboard",
                "display_name": "Dashboard",
                "icon": "bi-speedometer2",
                "url": "home",
                "type": "link",
                "roles": ["super_admin", "manager", "supervisor"]
            },
            {
                "name": "stats",
                "display_name": "Statistici",
                "icon": "bi-graph-up",
                "url": "stats",
                "type": "link",
                "roles": ["super_admin", "manager"]
            }
        ]
    },
    {
        "header": "Management",
        "items": [
            {
                "name": "users",
                "display_name": "Utilizatori",
                "icon": "bi-people",
                "type": "dropdown",
                "models": ["client", "vendor_company", "vendor_staff", "staff"],
                "roles": ["super_admin", "manager", "supervisor"]
            },
            {
                "name": "catalog",
                "display_name": "Catalog",
                "icon": "bi-box-seam",
                "type": "dropdown",
                "models": ["category", "product", "product_image", "product_price"],
                "roles": ["super_admin", "manager", "supervisor"]
            },
            {
                "name": "sales",
                "display_name": "Vânzări",
                "icon": "bi-cart-check",
                "type": "dropdown",
                "models": ["cart", "order", "invoice"],
                "roles": ["super_admin", "manager", "supervisor"]
            },
            {
                "name": "user_request",
                "display_name": "Cereri",
                "icon": "bi-envelope",
                "type": "single",
                "url": "user_request",
                "badge": "warning",  # Va arăta numărul de cereri neprocesate
                "roles": ["super_admin", "manager"]
            },
            {
                "name": "blog",
                "display_name": "Blog",
                "icon": "bi-newspaper",
                "type": "dropdown",
                "models": ["post", "post_image"],
                "roles": ["super_admin", "manager", "supervisor"]
            },
        ]
    },
    {
        "header": "Instrumente",
        "items": [
            {
                "name": "import",
                "display_name": "Import Date",
                "icon": "bi-upload",
                "url": "import",
                "type": "link",
                "roles": ["super_admin", "manager"]
            },
            {
                "name": "export",
                "display_name": "Export Date",
                "icon": "bi-download",
                "url": "export",
                "type": "link",
                "roles": ["super_admin", "manager", "supervisor"]
            },
            {
                "name": "activity",
                "display_name": "Jurnal Activitate",
                "icon": "bi-clock-history",
                "url": "activity",
                "type": "link",
                "roles": ["super_admin", "manager", "supervisor"]
            }
        ]
    },
    {
        "header": "Analytics",
        "items": [
            {
                "name": "settings",
                "display_name": "Analytics Overview",
                "icon": "bi-graph-up",
                "url": "analytics",
                "type": "link",
                "roles": ["super_admin", "manager"]
            },
            {
                "name": "analytics_users",
                "display_name": "Analiză Utilizatori",
                "icon": "bi-people",
                "url": "analytics/users",
                "type": "link",
                "roles": ["super_admin", "manager"]
            },
            {
                "name": "analytics_products",
                "display_name": "Analiză Produse",
                "icon": "bi-box-seam",
                "url": "analytics/products",
                "type": "link",
                "roles": ["super_admin", "manager"]
            }
        ]
    }
]

VENDOR_MODELS_CONFIG = {
    # CATALOG - Doar produsele companiei vendor
    "product": ModelConfig(
        name="product",
        display_name="Produsele Mele",
        icon="bi-box-seam",
        list_fields=["id", "sku", "name", "category_id", "is_active", "in_stock", "stock_quantity"],
        search_fields=["name", "sku", "description"],
        filter_fields=["category_id", "is_active", "in_stock"],
        required_fields=["name", "sku", "category_id"],
        unique_fields=["sku", "slug"],
        allow_import=True,
        allow_export=True,
        custom_actions=[
            {"name": "manage_images", "label": "Imagini", "icon": "bi-images"},
            {"name": "manage_prices", "label": "Prețuri", "icon": "bi-currency-dollar"},
            {"name": "duplicate", "label": "Duplică", "icon": "bi-copy"},
            {"name": "toggle_stock", "label": "În Stoc On/Off", "icon": "bi-toggle-on"}
        ]
    ),

    "product_image": ModelConfig(
        name="product_image",
        display_name="Imagini Produse",
        icon="bi-images",
        list_fields=["id", "product_id", "file_name", "is_primary", "sort_order"],
        search_fields=["file_name", "alt_text"],
        filter_fields=["product_id", "is_primary"],
        required_fields=["product_id", "image_path", "file_name"],
        allow_create=True,  # Vendor poate încărca imagini
        allow_update=True,
        allow_delete=True,  # Vendor poate șterge propriile imagini
        allow_import=False,
        allow_export=True
    ),

    "product_price": ModelConfig(
        name="product_price",
        display_name="Prețuri Produse",
        icon="bi-currency-dollar",
        list_fields=["id", "product_id", "price_type", "amount", "currency"],
        search_fields=["product_id"],
        filter_fields=["price_type"],
        required_fields=["product_id", "price_type", "amount"],
        allow_create=False,  # Se setează toate 4 prețurile odată
        allow_update=True,  # Poate actualiza prețuri
        allow_delete=False,  # Nu poate șterge prețuri
        allow_import=True,
        allow_export=True,
        custom_actions=[
            {"name": "bulk_update", "label": "Actualizare în masă", "icon": "bi-pencil-square"}
        ]
    ),

    # VÂNZĂRI - Doar pentru produsele companiei
    "cart": ModelConfig(
        name="cart",
        display_name="Coșuri cu Produsele Mele",
        icon="bi-cart",
        list_fields=["id", "cart_number", "client_id", "total_amount", "updated_at"],
        search_fields=["cart_number"],
        filter_fields=["updated_at"],
        required_fields=[],
        allow_create=False,
        allow_update=False,  # Nu poate modifica coșuri
        allow_delete=False,
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "view_details", "label": "Vezi Detalii", "icon": "bi-eye"}
        ]
    ),

    "order": ModelConfig(
        name="order",
        display_name="Comenzi cu Produsele Mele",
        icon="bi-cart-check",
        list_fields=["id", "order_number", "status", "total_amount", "created_at"],
        search_fields=["order_number"],
        filter_fields=["status", "created_at"],
        required_fields=[],
        allow_create=False,
        allow_update=False,  # Nu poate modifica comenzi
        allow_delete=False,
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "view_details", "label": "Vezi Detalii", "icon": "bi-eye"},
            {"name": "print", "label": "Printează", "icon": "bi-printer"}
        ]
    ),

    "invoice": ModelConfig(
        name="invoice",
        display_name="Facturi pentru Produsele Mele",
        icon="bi-receipt",
        list_fields=["id", "invoice_number", "invoice_type", "total_amount", "created_at"],
        search_fields=["invoice_number"],
        filter_fields=["invoice_type", "created_at"],
        required_fields=[],
        allow_create=False,
        allow_update=False,
        allow_delete=False,
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "download", "label": "Descarcă PDF", "icon": "bi-download"}
        ]
    ),

    # COMUNICARE
    "user_request": ModelConfig(
        name="user_request",
        display_name="Cereri pentru Produsele Mele",
        icon="bi-envelope",
        list_fields=["id", "request_type", "product_id", "is_processed", "created_at"],
        search_fields=["message"],
        filter_fields=["request_type", "is_processed"],
        required_fields=[],
        allow_create=False,
        allow_update=False,  # Nu poate edita cereri
        allow_delete=False,
        allow_import=False,
        allow_export=True,
        custom_actions=[
            {"name": "respond", "label": "Răspunde", "icon": "bi-reply"},
            {"name": "view_client", "label": "Vezi Client", "icon": "bi-person"}
        ]
    ),

    # SETĂRI COMPANIE
    "company_profile": ModelConfig(
        name="company_profile",
        display_name="Profil Companie",
        icon="bi-building",
        list_fields=[],  # Nu e listă, e pagină singulară
        search_fields=[],
        filter_fields=[],
        required_fields=["name", "legal_name", "tax_id", "email", "phone", "address"],
        allow_create=False,
        allow_update=True,  # Doar admin poate actualiza
        allow_delete=False,
        allow_import=False,
        allow_export=False
    )
}

VENDOR_MENU_STRUCTURE = [
    {
        "header": "Principal",
        "menu_items": [
            {
                "name": "dashboard",
                "display_name": "Dashboard",
                "icon": "bi-speedometer2",
                "url": "home",
                "type": "link",
                "roles": ["vendor_admin", "vendor_manager"]
            }
        ]
    },
    {
        "header": "Produse",
        "menu_items": [
            {
                "name": "products",
                "display_name": "Produsele Mele",
                "icon": "bi-box-seam",
                "url": "product",
                "type": "single",
                "roles": ["vendor_admin", "vendor_manager"]
            },
            {
                "name": "product_images",
                "display_name": "Galerie Imagini",
                "icon": "bi-images",
                "url": "product_image",
                "type": "single",
                "roles": ["vendor_admin", "vendor_manager"]
            },
            {
                "name": "product_prices",
                "display_name": "Gestionare Prețuri",
                "icon": "bi-currency-dollar",
                "url": "product_price",
                "type": "single",
                "roles": ["vendor_admin", "vendor_manager"]
            }
        ]
    },
    {
        "header": "Vânzări",
        "menu_items": [
            {
                "name": "carts",
                "display_name": "Coșuri Active",
                "icon": "bi-cart",
                "url": "cart",
                "type": "single",
                "badge": "info",  # Arată număr coșuri active
                "roles": ["vendor_admin", "vendor_manager"]
            },
            {
                "name": "orders",
                "display_name": "Comenzile Mele",
                "icon": "bi-cart-check",
                "url": "order",
                "type": "single",
                "badge": "danger",  # Arată comenzi noi
                "roles": ["vendor_admin", "vendor_manager"]
            },
            {
                "name": "invoices",
                "display_name": "Facturi",
                "icon": "bi-receipt",
                "url": "invoice",
                "type": "single",
                "roles": ["vendor_admin", "vendor_manager"]
            }
        ]
    },
    {
        "header": "Comunicare",
        "menu_items": [
            {
                "name": "requests",
                "display_name": "Cereri Clienți",
                "icon": "bi-envelope",
                "url": "user_request",
                "type": "single",
                "badge": "warning",  # Arată cereri neprocesate
                "roles": ["vendor_admin", "vendor_manager"]
            }
        ]
    },
    {
        "header": "Rapoarte",
        "menu_items": [
            {
                "name": "revenue",
                "display_name": "Venituri",
                "icon": "bi-cash-stack",
                "url": "revenue",
                "type": "link",
                "roles": ["vendor_admin"]
            },
            {
                "name": "analytics",
                "display_name": "Analize",
                "icon": "bi-bar-chart",
                "url": "analytics",
                "type": "link",
                "roles": ["vendor_admin", "vendor_manager"]
            },
            {
                "name": "export",
                "display_name": "Export Date",
                "icon": "bi-download",
                "url": "export",
                "type": "link",
                "roles": ["vendor_admin", "vendor_manager"]
            }
        ]
    }
]


def get_models_config(user_type: str) -> Dict[str, ModelConfig]:
    """Returnează models config bazat pe tipul de user."""
    if user_type == "staff":
        return STAFF_MODELS_CONFIG
    elif user_type == "vendor":
        return VENDOR_MODELS_CONFIG
    return {}

def get_menu_structure(user_type: str) -> List[Dict]:
    """Returnează menu structure bazat pe tipul de user."""
    if user_type == "staff":
        return STAFF_MENU_STRUCTURE
    elif user_type == "vendor":
        return VENDOR_MENU_STRUCTURE
    return []







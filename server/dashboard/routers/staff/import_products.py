# server/dashboard/routers/staff/import_products.py
"""
Router pentru import produse în Staff Dashboard.
Integrat cu structura existentă a dashboard-ului.
"""
import logging

import loging

logger = logging.getLogger("uvicorn.error")


from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

from cfg import get_db
from models import Staff, StaffRole, Product, ProductPrice, PriceType, Category
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local
from services.models.product_service import ProductService
from services.models.category_services import CategoryService

import_router = APIRouter()

templates = Jinja2Templates(directory="server/dashboard/templates/staf")
templates.env.filters['datetime_local'] = datetime_local

# Pydantic Models pentru validare
from pydantic import BaseModel, validator


class ImportPriceData(BaseModel):
    anonim: float
    user: float
    instalator: float
    pro: float

    @validator('*')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Prețul trebuie să fie pozitiv')
        return v


class ImportProductData(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category_id: int
    prices: ImportPriceData
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    in_stock: bool = True
    stock_quantity: int = 0

    @validator('sku')
    def validate_sku(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('SKU nu poate fi gol')
        return v.strip().upper()

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Numele produsului nu poate fi gol')
        return v.strip()


class ImportRequest(BaseModel):
    type: str  # 'general' sau 'category'
    category_id: Optional[int] = None
    products: List[ImportProductData]


@import_router.get("/", response_class=HTMLResponse)
async def import_page(
        request: Request,
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Afișează pagina de import produse."""
    # Verifică permisiuni
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nu aveți permisiunea de a importa produse"
        )

    if staff.role == StaffRole.MANAGER and not staff.can_manage_products:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nu aveți permisiunea de a gestiona produse"
        )

    # Obține categoriile pentru dropdown
    categories = await CategoryService.get_tree(db)

    # Flatten pentru dropdown
    flat_categories = []

    def flatten_category(cat, level=0):
        flat_categories.append({
            "id": cat.id,
            "name": f"{'  ' * level}{cat.name}",
            "slug": cat.slug,
            "level": level
        })
        for child in cat.children:
            flatten_category(child, level + 1)

    for cat in categories:
        flatten_category(cat)

    context = await get_template_context(request, staff, db)
    context.update({
        "categories": flat_categories,
        "page_title": "Import Produse"
    })

    return templates.TemplateResponse(
        "import/products.html",
        context
    )


@import_router.post("/preview")
async def preview_import(
        request: Request,
        file: UploadFile = File(...),
        import_type: str = Form(...),
        category_id: Optional[int] = Form(None),
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Preview pentru fișierul de import."""
    # Verifică permisiuni
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Nu aveți permisiuni")

    if staff.role == StaffRole.MANAGER and not staff.can_manage_products:
        raise HTTPException(status_code=403, detail="Nu aveți permisiuni pentru produse")

    # Verifică tipul fișierului
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Format invalid. Acceptăm doar .xlsx sau .xls"
        )

    try:
        # Citește Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # Validare și procesare
        products = []
        errors = []

        # Mapare coloane Excel -> câmpuri sistem
        column_mapping = {
            'SKU': 'sku',
            'Nume': 'name',
            'Descriere': 'description',
            'Descriere Scurtă': 'short_description',
            'ID Categorie': 'category_id',
            'Preț Anonim': 'price_anonim',
            'Preț User': 'price_user',
            'Preț Instalator': 'price_instalator',
            'Preț Pro': 'price_pro',
            'Meta Title': 'meta_title',
            'Meta Description': 'meta_description',
            'În Stoc': 'in_stock',
            'Cantitate': 'stock_quantity'
        }

        # Verifică categoriile valide
        valid_category_ids = set()
        if import_type == 'general':
            # Obține toate ID-urile de categorii din Excel
            category_ids = []
            if 'ID Categorie' in df.columns:
                category_ids = df['ID Categorie'].dropna().unique().tolist()
                # Convertește la int
                category_ids = [int(float(x)) for x in category_ids if pd.notna(x)]

                result = await db.execute(
                    select(Category.id).where(Category.id.in_(category_ids))
                )
                valid_category_ids = set(row[0] for row in result)

        for idx, row in df.iterrows():
            product_data = {
                'row': idx + 2,  # Excel row number
                'errors': [],
                'warnings': []
            }

            # Extrage datele
            for excel_col, system_field in column_mapping.items():
                if excel_col in df.columns:
                    value = row.get(excel_col)
                    if pd.notna(value):
                        # Conversii specifice pe tip de câmp
                        if system_field == 'category_id':
                            product_data[system_field] = int(float(value))
                        elif system_field in ['price_anonim', 'price_user', 'price_instalator', 'price_pro']:
                            product_data[system_field] = float(value)
                        elif system_field == 'stock_quantity':
                            product_data[system_field] = int(float(value))
                        elif system_field == 'in_stock':
                            # Convertește DA/NU în boolean
                            if isinstance(value, str):
                                product_data[system_field] = value.upper() in ['DA', 'YES', 'TRUE', '1']
                            else:
                                product_data[system_field] = bool(value)
                        else:
                            product_data[system_field] = str(value) if not isinstance(value, str) else value

            # Pentru import per categorie
            if import_type == 'category' and category_id:
                product_data['category_id'] = category_id

            # Validări
            if not product_data.get('sku'):
                product_data['errors'].append('SKU lipsă')
            else:
                # Verifică unicitate SKU
                existing = await db.execute(
                    select(Product).where(Product.sku == product_data['sku'])
                )
                if existing.scalar_one_or_none():
                    product_data['errors'].append(f"SKU {product_data['sku']} există deja")

            if not product_data.get('name'):
                product_data['errors'].append('Nume lipsă')

            # Validare prețuri
            for price_type in ['price_anonim', 'price_user', 'price_instalator', 'price_pro']:
                if not product_data.get(price_type) or product_data.get(price_type, 0) <= 0:
                    product_data['errors'].append(f'{price_type.replace("_", " ").title()} invalid')

            # Validare categorie pentru import general
            if import_type == 'general':
                if not product_data.get('category_id'):
                    product_data['errors'].append('ID categorie lipsă')
                elif int(product_data.get('category_id', 0)) not in valid_category_ids:
                    product_data['errors'].append(f"Categoria {product_data.get('category_id')} nu există")

            # Warnings pentru logica prețuri
            if all(product_data.get(p, 0) > 0 for p in ['price_anonim', 'price_user', 'price_instalator', 'price_pro']):
                if product_data['price_user'] >= product_data['price_anonim']:
                    product_data['warnings'].append('Preț user >= preț anonim')
                if product_data['price_instalator'] >= product_data['price_user']:
                    product_data['warnings'].append('Preț instalator >= preț user')
                if product_data['price_pro'] >= product_data['price_instalator']:
                    product_data['warnings'].append('Preț pro >= preț instalator')

            products.append(product_data)

        # Statistici
        valid_count = len([p for p in products if not p['errors']])
        error_count = len([p for p in products if p['errors']])

        return JSONResponse({
            "success": True,
            "products": products,
            "stats": {
                "total": len(products),
                "valid": valid_count,
                "errors": error_count
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Eroare la procesarea fișierului: {str(e)}"
        }, status_code=400)


@import_router.post("/process")
async def process_import(
        request: Request,
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Procesează importul efectiv."""
    # Verifică permisiuni
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(status_code=403)

    if staff.role == StaffRole.MANAGER and not staff.can_manage_products:
        raise HTTPException(status_code=403)

    try:
        # Obține datele din request
        data = await request.json()
        import_type = data.get('type')
        category_id = data.get('category_id')
        products_data = data.get('products', [])

        results = {
            'success': 0,
            'failed': 0,
            'details': []
        }

        # Procesează fiecare produs
        for idx, product_data in enumerate(products_data):
            try:
                logger.info(f"Processing product {idx + 1}: SKU={product_data.get('sku')}")

                # Generează slug
                from slugify import slugify
                base_slug = slugify(product_data['name'])
                slug = base_slug
                counter = 1

                # Verifică unicitate slug
                while True:
                    existing_slug = await db.execute(
                        select(Product).where(Product.slug == slug)
                    )
                    if not existing_slug.scalar_one_or_none():
                        break
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Creează produsul
                product = Product(
                    vendor_company_id=1,  # System Vendor în MVP
                    category_id=product_data.get('category_id', category_id),
                    name=product_data['name'],
                    slug=slug,
                    sku=product_data['sku'],
                    description=product_data.get('description'),
                    short_description=product_data.get('short_description'),
                    in_stock=product_data.get('in_stock', True),
                    stock_quantity=product_data.get('stock_quantity', 0),
                    meta_title=product_data.get('meta_title') or product_data['name'],
                    meta_description=product_data.get('meta_description'),
                    sort_order=0
                )
                db.add(product)
                await db.flush()

                # Adaugă prețurile
                price_mapping = {
                    PriceType.ANONIM: float(product_data.get('price_anonim', 0)),
                    PriceType.USER: float(product_data.get('price_user', 0)),
                    PriceType.INSTALATOR: float(product_data.get('price_instalator', 0)),
                    PriceType.PRO: float(product_data.get('price_pro', 0))
                }

                for price_type, amount in price_mapping.items():
                    price = ProductPrice(
                        product_id=product.id,
                        price_type=price_type,
                        amount=amount,
                        currency="MDL"
                    )
                    db.add(price)

                results['success'] += 1
                results['details'].append({
                    'row': product_data.get('row', 0),
                    'sku': product_data['sku'],
                    'status': 'success',
                    'product_id': product.id
                })

            except Exception as e:
                logger.error(f"Error processing product {idx + 1}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

                results['failed'] += 1
                results['details'].append({
                    'row': product_data.get('row', 0),
                    'sku': product_data.get('sku', 'N/A'),
                    'status': 'error',
                    'message': str(e)
                })

        # Commit toate modificările
        await db.commit()

        return JSONResponse({
            "success": True,
            "results": results
        })

    except Exception as e:
        logger.error(f"Fatal error in import: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        await db.rollback()
        return JSONResponse({
            "success": False,
            "error": f"Eroare la import: {str(e)}"
        }, status_code=500)


@import_router.get("/template/{import_type}")
async def download_template(
        import_type: str,
        staff: Staff = Depends(get_current_staff)
):
    """Descarcă template Excel pentru import."""
    from fastapi.responses import StreamingResponse
    import pandas as pd
    import io

    if import_type == 'general':
        template_data = {
            'SKU': ['PROD001', 'PROD002'],
            'Nume': ['Produs Exemplu 1', 'Produs Exemplu 2'],
            'Descriere': ['Descriere detaliată produs 1', 'Descriere detaliată produs 2'],
            'Descriere Scurtă': ['Scurt 1', 'Scurt 2'],
            'ID Categorie': [1, 2],
            'Preț Anonim': [100.00, 200.00],
            'Preț User': [90.00, 180.00],
            'Preț Instalator': [80.00, 160.00],
            'Preț Pro': [70.00, 140.00],
            'Meta Title': ['SEO Title 1', 'SEO Title 2'],
            'Meta Description': ['SEO Desc 1', 'SEO Desc 2'],
            'În Stoc': ['DA', 'DA'],
            'Cantitate': [50, 100]
        }
    else:
        # Template pentru import per categorie (fără ID Categorie)
        template_data = {
            'SKU': ['PROD001', 'PROD002'],
            'Nume': ['Produs Exemplu 1', 'Produs Exemplu 2'],
            'Descriere': ['Descriere detaliată produs 1', 'Descriere detaliată produs 2'],
            'Descriere Scurtă': ['Scurt 1', 'Scurt 2'],
            'Preț Anonim': [100.00, 200.00],
            'Preț User': [90.00, 180.00],
            'Preț Instalator': [80.00, 160.00],
            'Preț Pro': [70.00, 140.00],
            'Meta Title': ['SEO Title 1', 'SEO Title 2'],
            'Meta Description': ['SEO Desc 1', 'SEO Desc 2'],
            'În Stoc': ['DA', 'DA'],
            'Cantitate': [50, 100]
        }

    # Creează DataFrame și exportă ca Excel
    df = pd.DataFrame(template_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Template', index=False)

        # Formatare
        workbook = writer.book
        worksheet = writer.sheets['Template']

        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })

        # Aplică format la header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)

        # Ajustează lățimea coloanelor
        for i, col in enumerate(df.columns):
            column_len = df[col].astype(str).str.len().max()
            column_len = max(column_len, len(col)) + 2
            worksheet.set_column(i, i, column_len)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=template_import_{import_type}.xlsx'
        }
    )
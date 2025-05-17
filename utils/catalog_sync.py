from sqlalchemy import select, exists, and_, update, delete
from models.catalog import Category, Product
from app import app_state   # obiect global simplu

async def sync_catalog(session: AsyncSession) -> None:
    # 1. orfane
    orphans = (await session.scalars(select(Product).where(Product.category_id.is_(None)))).all()

    # 2. unknown
    unknown = await session.scalar(select(Category).where(Category.is_unknown.is_(True)))
    if orphans and not unknown:
        unknown = Category(name="Necategorizate", slug="unknown", is_unknown=True)
        session.add(unknown)
        await session.flush()          # obţine id‑ul

    # 3. mutare
    if orphans:
        await session.execute(
            update(Product)
            .where(Product.id.in_([p.id for p in orphans]))
            .values(category_id=unknown.id)
        )

    # 4. ştergere categorii goale (exclus unknown)
    empty_q = select(Category.id).where(
        and_(
            Category.is_unknown.is_(False),
            ~exists().where(Product.category_id == Category.id)
        )
    )
    for cat_id in (await session.scalars(empty_q)).all():
        await session.execute(delete(Category).where(Category.id == cat_id))

    # 5. home‑page mode
    has_normal_cat = await session.scalar(
        exists().where(
            and_(
                Category.is_unknown.is_(False),
                exists().where(Product.category_id == Category.id)
            )
        ).select()
    )
    app_state.homepage_mode = "categories" if has_normal_cat else "products"
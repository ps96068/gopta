from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Enum, Integer, ForeignKey, Numeric, DateTime, func, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates


from cfg import Base
from models.base import CreatedAtMixin
from models.catalog.product_price import PriceType


# catalog/sale/order_item.py


class OrderItem(Base, CreatedAtMixin):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_quantity_positive"),
        UniqueConstraint("order_id", "product_id", name="uix_order_product"),
        Index("ix_order_id", "order_id"),
    )

    # ---------- Keys ----------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    # ---------- Business data ----------
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    price_usd_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_mdl_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rate_used: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    price_type_snapshot: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)

    # ---------- Relationships ----------
    order: Mapped["Order"] = relationship(
        "Order", back_populates="items", foreign_keys=[order_id]
    )
    product: Mapped["Product"] = relationship(
        "Product", back_populates="order_items", foreign_keys=[product_id]
    )

    # ---------- Properties ----------
    @property
    def total_price_mdl(self) -> Decimal:
        return self.price_mdl_snapshot * self.quantity

    @property
    def total_price_usd(self) -> Decimal:
        return self.price_usd_snapshot * self.quantity

    # ---------- Validators ----------
    @validates("quantity")
    def validate_quantity(self, key, value: int):
        if value <= 0:
            raise ValueError("Cantitatea trebuie să fie un număr pozitiv")
        if value > 1000:
            raise ValueError("Cantitatea este prea mare pentru o singură comandă")
        return value

    @validates("price_usd_snapshot", "price_mdl_snapshot")
    def validate_price(self, key, value: Decimal):
        if value < 0:
            raise ValueError("Prețul trebuie să fie pozitiv")
        return value

    # ---------- Repr ----------
    def __repr__(self):
        return (
            f"<OrderItem(id={self.id}, product={self.product_id}, "
            f"qty={self.quantity}, price_mdl={self.price_mdl_snapshot})>"
        )


    # # Dacă doriți să afișați product_id
    # def __repr__(self):
    #     return f"<OrderItem(id={self.id}, product_id='{self.product_id}', quantity={self.quantity})>"
    #
    # # Dacă doriți să afișați numele produsului
    # def __repr__(self):
    #     return f"<OrderItem(id={self.id}, product_name='{self.product.name}', quantity={self.quantity})>"


"""

# Implementarea unei Metode pentru Actualizarea Prețului verifică și setează prețul curent
def create_order_item(session, order_id: int, product_id: int, quantity: int, price_type: PriceType, staff_id: int):
    # Obținem prețul curent al produsului pentru tipul de client
    product_price = session.query(ProductPrice).filter(
        ProductPrice.product_id == product_id,
        ProductPrice.price_type == price_type
    ).first()

    if not product_price:
        raise ValueError(f"Nu există un preț setat pentru produsul cu ID {product_id} și tipul de preț {price_type}")

    # Creăm articolul de comandă cu prețul curent
    order_item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        price_per_unit=product_price.price,
        create_date=datetime.now(),
        modified_date=datetime.now(),
    )

    session.add(order_item)
    session.commit()

    return order_item



"""




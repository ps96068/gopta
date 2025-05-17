import re
import enum
from datetime import datetime
from starlette.requests import Request
from sqlalchemy import Boolean, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column, Relationship
from sqlalchemy.sql import func


from database import Base
# from .user import User


class CompanyStatus(enum.Enum):
    pro = "pro"
    instal = "instal"



class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # new
    created_by: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), nullable=False)

    address: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)

    # new
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus), nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )


    # Relații
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="company")
    creator: Mapped["Staff"] = relationship("Staff", foreign_keys=[created_by], back_populates="companies_created")


    @validates('phone_number')
    def validate_phone(self, key, number):
        if number:
            if not re.match(r"^\+?[0-9]{1,13}$", number):
                raise ValueError("Numărul de telefon are un format invalid")
        return number

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Adresa de email este invalidă")
        return email

    async def __admin_repr__(self, request: Request):
    # async def __admin_select2_repr__(self, request: Request):
    #     return f"<div>{self.name}</div>"
        return f"{self.name}"


    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', email='{self.email}')>"

    def __str__(self):
        return f"{self.name} - {self.id}"





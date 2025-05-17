from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


# ─────────── Base ───────────
class PostBase(BaseModel):
    title: str = Field(..., description="Titlul articolului")
    content: str = Field(..., description="Conținutul articolului")
    author_id: int = Field(..., description="ID-ul staff-ului care a creat postarea")
    publish_date: datetime = Field(..., description="Data și ora publicării")
    is_active: bool = Field(..., description="Flag dacă postarea este activă")


# ─────────── Create ───────────
class PostCreate(PostBase):
    """
    Folosit la POST /posts
    """


# ─────────── Update ───────────
class PostUpdate(BaseModel):
    title: str | None = Field(None, description="Titlul articolului")
    content: str | None = Field(None, description="Conținutul articolului")
    publish_date: datetime | None = Field(None, description="Data și ora publicării")
    is_active: bool | None = Field(None, description="Flag dacă postarea este activă")


# ─────────── Read ───────────
class PostRead(PostBase):
    id: int
    modified_by: int | None = Field(None, description="ID-ul staff-ului care a modificat ultima oară")
    created_at: datetime = Field(..., description="Timestamp creării")
    updated_at: datetime | None = Field(None, description="Timestamp ultimei modificări")

    class Config:
        from_attributes = True
        # Pentru relații nested adaugam:
        # allow_population_by_field_name = True
        # arbitrary_types_allowed = True
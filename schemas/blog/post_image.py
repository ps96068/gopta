from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class PostImageBase(BaseModel):
    post_id: int | None = Field(None, description="ID-ul articolului")
    author_id: int = Field(..., description="ID staff care a încărcat imaginea")
    image_path: str = Field(..., description="Calea către fișierul imaginii")
    is_primary: bool = Field(False, description="Flag dacă este imaginea principală")


class PostImageCreate(PostImageBase):
    pass


class PostImageRead(PostImageBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
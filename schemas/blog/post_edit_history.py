from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from models.blog.post_edit_history import ModificationTypeEnum

class PostEditHistoryRead(BaseModel):
    id: int
    post_id: int
    changed_by: int | None = Field(None, description="ID staff care a modificat")
    modification_type: ModificationTypeEnum = Field(..., description="Tipul modificării")
    old_content: str | None = Field(None, description="Conținutul anterior modificării")
    created_at: datetime = Field(..., description="Data și ora modificării")

    class Config:
        from_attributes = True
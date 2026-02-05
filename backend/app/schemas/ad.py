from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AdBase(BaseModel):
    title: str
    image_url: str
    media_type: str = "image"
    target_url: Optional[str] = None
    is_active: bool = True
    duration_seconds: int = 15

class AdCreate(AdBase):
    pass

class AdRead(AdBase):
    id: UUID

    class Config:
        from_attributes = True

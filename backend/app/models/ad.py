import uuid
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Ad(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    media_type = Column(String, default="image") # image | video
    target_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    duration_seconds = Column(Integer, default=15)

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import DateTime, Boolean, String
from datetime import datetime

class Base(DeclarativeBase):
    pass 

class Spine(Base):
    __abstract__ = True  
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=lambda: True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=lambda: False)
    deleted_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String, nullable=True)

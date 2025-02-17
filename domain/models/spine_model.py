from sqlalchemy import Column, DateTime, Boolean, String
from datetime import datetime
from utils.database import Base

class Spine(Base):
    __abstract__ = True  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    deleted_reason = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)

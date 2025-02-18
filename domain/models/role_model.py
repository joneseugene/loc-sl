

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .spine_model import Spine

class Role(Spine):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    users = relationship("User", back_populates="role")


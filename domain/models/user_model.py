from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from .spine_model import Spine

class User(Spine):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    organization = Column(String)
    password = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"), default=3)

    role = relationship("Role", back_populates="users")

# models/district_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .spine_model import Spine

class Constituency(Spine):
    __tablename__ = "constituencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    district_id = Column(Integer, ForeignKey("districts.id"))
    district = relationship("District", back_populates="constituencies")

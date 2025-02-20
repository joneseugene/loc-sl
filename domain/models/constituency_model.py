# models/district_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .spine_model import Spine

class Constituency(Spine):
    __tablename__ = "constituencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    region_id = Column(Integer, ForeignKey("regions.id"))
    district_id = Column(Integer, ForeignKey("districts.id"))
    # Relationships
    region = relationship("Region", back_populates="constituencies")
    district = relationship("District", back_populates="constituencies")
    wards = relationship("Ward", back_populates="constituency")

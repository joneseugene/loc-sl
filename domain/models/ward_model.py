# models/district_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .spine_model import Spine

class Ward(Spine):
    __tablename__ = "ward"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    region_id = Column(Integer, ForeignKey("regions.id"))
    district_id = Column(Integer, ForeignKey("districts.id"))
    constituency_id = Column(Integer, ForeignKey("constituencies.id"))
    region = relationship("Region", back_populates="wards")
    district = relationship("District", back_populates="wards")
    constituency = relationship("Constituency", back_populates="wards")

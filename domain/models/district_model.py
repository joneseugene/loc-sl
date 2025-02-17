# models/district_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .spine_model import Spine

class District(Spine):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    region_id = Column(Integer, ForeignKey("regions.id"))
    region = relationship("Region", back_populates="districts")

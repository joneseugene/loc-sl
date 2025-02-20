# models/district_model.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, event
from sqlalchemy.orm import relationship

from utils.functions import generate_slug
from .spine_model import Spine

class District(Spine):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    region_id = Column(Integer, ForeignKey("regions.id"))
    
    # References 
    region = relationship("Region", back_populates="districts")
    constituencies = relationship("Constituency", back_populates="district")
    wards = relationship("Ward", back_populates="district")
    

# Event listeners to auto-generate slug
event.listen(District, "before_insert", generate_slug)
event.listen(District, "before_update", generate_slug)

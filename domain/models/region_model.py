

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from .spine_model import Spine
from .district_model import District

class Region(Spine):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)
    districts = relationship("District", back_populates="region")
    constituencies = relationship("Constituency", back_populates="region")
    wards = relationship("Ward", back_populates="region")  

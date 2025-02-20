

from sqlalchemy import Column, Integer, String, Float, event
from sqlalchemy.orm import relationship

from utils.functions import generate_slug
from .spine_model import Spine

class Region(Spine):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    lon = Column(Float)
    lat = Column(Float)

    districts = relationship("District", back_populates="region")
    constituencies = relationship("Constituency", back_populates="region")
    wards = relationship("Ward", back_populates="region")  

from .district_model import District
from .constituency_model import Constituency
from .ward_model import Ward

# Event listeners to auto-generate slug
event.listen(Region, "before_insert", generate_slug)
event.listen(Region, "before_update", generate_slug)
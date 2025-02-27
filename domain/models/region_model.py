from sqlalchemy import Integer, String, Float, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.functions import generate_slug
from .spine_model import Spine

class Region(Spine):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    districts: Mapped[list["District"]] = relationship("District", back_populates="region", cascade="all, delete-orphan")
    constituencies: Mapped[list["Constituency"]] = relationship("Constituency", back_populates="region", cascade="all, delete-orphan")
    chiefdoms: Mapped[list["Chiefdom"]] = relationship("Chiefdom", back_populates="region", cascade="all, delete-orphan")
    wards: Mapped[list["Ward"]] = relationship("Ward", back_populates="region", cascade="all, delete-orphan")

# Import models
from .district_model import District
from .constituency_model import Constituency
from .chiefdom_model import Chiefdom
from .ward_model import Ward

# Event listeners
event.listen(Region, "before_insert", generate_slug)
event.listen(Region, "before_update", generate_slug)

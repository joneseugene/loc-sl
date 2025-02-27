from sqlalchemy import Integer, String, Float, ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.functions import generate_slug
from .spine_model import Spine

class District(Spine):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    region_id: Mapped[int| None] = mapped_column(Integer, ForeignKey("regions.id"))

    # Relationships (Updated)
    region: Mapped["Region"] = relationship(back_populates="districts")
    constituencies: Mapped[list["Constituency"]] = relationship(back_populates="district", cascade="all, delete-orphan")
    chiefdoms: Mapped[list["Chiefdom"]] = relationship(back_populates="district", cascade="all, delete-orphan")
    wards: Mapped[list["Ward"]] = relationship(back_populates="district", cascade="all, delete-orphan")

# Import models
from .region_model import Region
from .constituency_model import Constituency
from .chiefdom_model import Chiefdom
from .ward_model import Ward

# Event listeners
event.listen(District, "before_insert", generate_slug)
event.listen(District, "before_update", generate_slug)

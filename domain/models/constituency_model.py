from sqlalchemy import Integer, String, Float, ForeignKey, event
from utils.functions import generate_slug
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .spine_model import Spine

class Constituency(Spine):
    __tablename__ = "constituencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"))
    district_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("districts.id"))

    # Relationships
    region: Mapped["Region"] = relationship(back_populates="constituencies")
    district: Mapped["District"] = relationship(back_populates="constituencies")
    wards: Mapped[list["Ward"]] = relationship(back_populates="constituency", cascade="all, delete-orphan")

    # Import models
from .region_model import Region
from .district_model import District
from .ward_model import Ward

# Event listeners
event.listen(Constituency, "before_insert", generate_slug)
event.listen(Constituency, "before_update", generate_slug)

from sqlalchemy import Integer, String, Float, ForeignKey, event
from utils.functions import generate_slug
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .spine_model import Spine

class Ward(Spine):
    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"))
    district_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("districts.id"))
    constituency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("constituencies.id"))

    # Relationships
    region: Mapped["Region"] = relationship(back_populates="wards")
    district: Mapped["District"] = relationship(back_populates="wards")
    constituency: Mapped["Constituency"] = relationship(back_populates="wards")

    # Import models
from .region_model import Region
from .district_model import District
from .constituency_model import Constituency

# Event listeners
event.listen(Region, "before_insert", generate_slug)
event.listen(Region, "before_update", generate_slug)
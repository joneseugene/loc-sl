from sqlalchemy import Integer, String, Float, ForeignKey, event
from utils.functions import generate_slug
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .spine_model import Spine

class Chiefdom(Spine):
    __tablename__ = "chiefdoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"))
    district_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("districts.id"))

    # Relationships
    region: Mapped["Region"] = relationship(back_populates="chiefdoms")
    district: Mapped["District"] = relationship(back_populates="chiefdoms")

# Import models
from .district_model import District
from .region_model import Region

# Event listeners
event.listen(Chiefdom, "before_insert", generate_slug)
event.listen(Chiefdom, "before_update", generate_slug)

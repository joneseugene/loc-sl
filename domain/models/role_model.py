

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .spine_model import Spine

class Role(Spine):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    users = relationship("User", back_populates="role", passive_deletes=True)

    


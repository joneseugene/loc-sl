from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .spine_model import Spine

class User(Spine):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    organization: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    password: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, default=3)
    role = relationship("Role", back_populates="users")

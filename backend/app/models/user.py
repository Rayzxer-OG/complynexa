"""User model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    """User model with password hash for JWT auth."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    documents = relationship("Document", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

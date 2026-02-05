# src/services/auth_models.py
"""User and authentication models."""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from src.services.models import Base


class UserRole(str, Enum):
    """User roles enumeration."""

    USER = "user"
    ADMIN = "admin"
    SYSADMIN = "sysadmin"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationship with conversations (optional - for user-specific conversations)
    # conversations = relationship("Conversation", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def is_sysadmin(self) -> bool:
        """Check if user is a system administrator."""
        return self.role == UserRole.SYSADMIN.value

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin or sysadmin."""
        return self.role in (UserRole.ADMIN.value, UserRole.SYSADMIN.value)

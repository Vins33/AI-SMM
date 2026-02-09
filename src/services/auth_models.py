# src/services/auth_models.py
"""User and authentication models."""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

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
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationship with conversations
    conversations = relationship("Conversation", back_populates="user")

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


class TokenBlacklist(Base):
    """Blacklisted JWT tokens (for logout / revocation)."""

    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    """Audit log for tracking admin and security-relevant actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)  # e.g. "user", "conversation"
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

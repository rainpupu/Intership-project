from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    avatar = Column(String(500), nullable=True)
    role = Column(String(20), default="user", nullable=False, index=True)
    campus_role = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class Cat(Base):
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    cover_image = Column(String(500), nullable=True)
    gallery_images = Column(JSON, default=list)
    coat_color = Column(String(100), nullable=True, index=True)
    age_stage = Column(String(50), nullable=True, index=True)
    gender = Column(String(20), nullable=True)
    personality_tags = Column(JSON, default=list)
    health_status = Column(String(100), nullable=True, index=True)
    mood_status = Column(String(100), nullable=True)
    adoption_status = Column(String(50), default="暂不开放", nullable=False, index=True)
    last_seen_location = Column(String(200), nullable=True, index=True)
    last_seen_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    is_focus = Column(Boolean, default=False, nullable=False, index=True)
    mark_type = Column(String(50), nullable=True)
    mark_remark = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    observations = relationship("CatObservation", back_populates="cat", cascade="all, delete-orphan")
    audit_records = relationship("CatAuditRecord", back_populates="cat", cascade="all, delete-orphan")


class CatObservation(Base):
    __tablename__ = "cat_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    location = Column(String(200), nullable=True)
    mood_status = Column(String(100), nullable=True)
    health_status = Column(String(100), nullable=True)
    observed_at = Column(DateTime, default=datetime.now, index=True)
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

    cat = relationship("Cat", back_populates="observations")


class CatAuditRecord(Base):
    __tablename__ = "cat_audit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    remark = Column(Text, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    operator_name = Column(String(100), nullable=True)
    operated_at = Column(DateTime, default=datetime.now, index=True)

    cat = relationship("Cat", back_populates="audit_records")

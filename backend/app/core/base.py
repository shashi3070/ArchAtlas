"""Shared SQLAlchemy declarative base for all persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

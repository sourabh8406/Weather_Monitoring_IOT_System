"""SQLAlchemy ORM model for the settings table."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    temperature_limit: Mapped[float] = mapped_column(Float, nullable=False, default=35.0)
    humidity_limit: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    air_quality_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    refresh_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    device_timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

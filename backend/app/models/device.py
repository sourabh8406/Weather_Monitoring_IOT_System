"""SQLAlchemy ORM model for the devices table."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class DeviceStatus(str, enum.Enum):
    online = "online"
    offline = "offline"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus), nullable=False, default=DeviceStatus.offline
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

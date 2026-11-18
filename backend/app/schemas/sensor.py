"""Pydantic v2 schemas for sensor readings, alerts, devices, and settings."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Sensor Readings
# ---------------------------------------------------------------------------

class SensorReadingCreate(BaseModel):
    device_code: str = Field(min_length=1, max_length=100)
    temperature: float
    humidity: float
    pressure: float
    rain_detected: bool
    air_quality_raw: int


class SensorReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    rain_detected: Optional[bool]
    air_quality_raw: Optional[int]
    created_at: datetime


class SensorLatest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    device_code: str
    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]
    rain_detected: Optional[bool]
    air_quality_raw: Optional[int]
    created_at: datetime


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertCreate(BaseModel):
    device_id: int
    alert_type: str
    message: str
    severity: str  # 'critical' | 'warning' | 'info'


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    alert_type: str
    message: Optional[str]
    severity: str
    is_read: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_name: str
    device_code: str
    location: Optional[str]
    status: str
    last_seen: Optional[datetime]


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    temperature_limit: float
    humidity_limit: float
    air_quality_limit: int
    refresh_interval: int
    device_timeout: int
    updated_at: datetime


class SettingsUpdate(BaseModel):
    temperature_limit: Optional[float] = Field(None, ge=-40, le=85)
    humidity_limit: Optional[float] = Field(None, ge=0, le=100)
    air_quality_limit: Optional[int] = Field(None, ge=0, le=4095)
    refresh_interval: Optional[int] = Field(None, ge=1, le=3600)
    device_timeout: Optional[int] = Field(None, ge=5, le=86400)

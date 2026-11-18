"""Sensor service — validates and persists incoming sensor readings."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceStatus
from app.models.reading import SensorReading
from app.models.settings import Settings
from app.schemas.sensor import SensorReadingCreate
from app.services import alert_service


# ---------------------------------------------------------------------------
# Validation ranges (physical sensor limits for ESP32 + common sensors)
# ---------------------------------------------------------------------------
_TEMP_MIN, _TEMP_MAX = -40.0, 85.0
_HUM_MIN, _HUM_MAX = 0.0, 100.0
_PRES_MIN, _PRES_MAX = 300.0, 1100.0
_AQI_MIN, _AQI_MAX = 0, 4095


def _validate_ranges(data: SensorReadingCreate) -> None:
    errors = []
    if not (_TEMP_MIN <= data.temperature <= _TEMP_MAX):
        errors.append(
            f"temperature {data.temperature} out of range [{_TEMP_MIN}, {_TEMP_MAX}]"
        )
    if not (_HUM_MIN <= data.humidity <= _HUM_MAX):
        errors.append(
            f"humidity {data.humidity} out of range [{_HUM_MIN}, {_HUM_MAX}]"
        )
    if not (_PRES_MIN <= data.pressure <= _PRES_MAX):
        errors.append(
            f"pressure {data.pressure} out of range [{_PRES_MIN}, {_PRES_MAX}]"
        )
    if not (_AQI_MIN <= data.air_quality_raw <= _AQI_MAX):
        errors.append(
            f"air_quality_raw {data.air_quality_raw} out of range [{_AQI_MIN}, {_AQI_MAX}]"
        )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Sensor value out of valid range", "errors": errors},
        )


def save_reading(db: Session, data: SensorReadingCreate) -> SensorReading:
    """
    1. Validate sensor data ranges.
    2. Resolve device_code → Device row (auto-create if unknown).
    3. Persist SensorReading.
    4. Update device last_seen / status.
    5. Check alert thresholds.
    """
    _validate_ranges(data)

    # Resolve device
    device: Device | None = (
        db.query(Device).filter(Device.device_code == data.device_code).first()
    )
    if device is None:
        device = Device(
            device_name=data.device_code,
            device_code=data.device_code,
            status=DeviceStatus.online,
        )
        db.add(device)
        db.flush()

    # Update heartbeat
    device.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
    device.status = DeviceStatus.online

    # Persist reading
    reading = SensorReading(
        device_id=device.id,
        temperature=data.temperature,
        humidity=data.humidity,
        pressure=data.pressure,
        rain_detected=data.rain_detected,
        air_quality_raw=data.air_quality_raw,
    )
    db.add(reading)
    db.flush()  # get reading.id before alert check

    # Load current settings (use first row; fall back to defaults)
    settings: Settings | None = db.query(Settings).first()
    if settings is None:
        settings = Settings()

    # Check and create alerts
    alert_service.check_and_create_alerts(db, reading, settings)

    db.commit()
    db.refresh(reading)
    return reading

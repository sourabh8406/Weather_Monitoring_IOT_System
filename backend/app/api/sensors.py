"""Sensors router — ingest readings and query history."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.device import Device
from app.models.reading import SensorReading
from app.models.user import User
from app.schemas.sensor import SensorLatest, SensorReadingCreate, SensorReadingResponse
from app.services import sensor_service

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("/public-summary")
def public_summary(db: Session = Depends(get_db)):
    """Small read-only snapshot for the public landing page."""
    reading = db.query(SensorReading).order_by(SensorReading.created_at.desc()).first()
    return {
        "device_count": db.query(Device).count(),
        "reading_count": db.query(SensorReading).count(),
        "latest": ({"temperature": reading.temperature, "humidity": reading.humidity,
                    "pressure": reading.pressure, "air_quality_raw": reading.air_quality_raw}
                   if reading else None),
    }


@router.post("/readings", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def ingest_reading(payload: SensorReadingCreate, db: Session = Depends(get_db)):
    """ESP32 posts sensor data here — no authentication required."""
    reading = sensor_service.save_reading(db, payload)
    return reading


@router.get("/latest", response_model=SensorLatest)
def get_latest(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return the most recent sensor reading across all devices."""
    reading = (
        db.query(SensorReading)
        .order_by(SensorReading.created_at.desc())
        .first()
    )
    if reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No readings found")

    device = db.query(Device).filter(Device.id == reading.device_id).first()
    return SensorLatest(
        id=reading.id,
        device_id=reading.device_id,
        device_code=device.device_code if device else "unknown",
        temperature=reading.temperature,
        humidity=reading.humidity,
        pressure=reading.pressure,
        rain_detected=reading.rain_detected,
        air_quality_raw=reading.air_quality_raw,
        created_at=reading.created_at,
    )


@router.get("/history", response_model=list[SensorReadingResponse])
def get_history(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return historical readings filtered by date range, newest first."""
    q = db.query(SensorReading)
    if start_date:
        q = q.filter(SensorReading.created_at >= start_date)
    if end_date:
        q = q.filter(SensorReading.created_at <= end_date)
    readings = q.order_by(SensorReading.created_at.desc()).limit(limit).all()
    return list(reversed(readings))


@router.get("/status")
def get_sensor_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return count of total readings and latest reading timestamp."""
    total = db.query(SensorReading).count()
    latest = (
        db.query(SensorReading)
        .order_by(SensorReading.created_at.desc())
        .first()
    )
    return {
        "total_readings": total,
        "latest_reading_at": latest.created_at if latest else None,
    }

"""Devices router."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.device import Device
from app.models.settings import Settings
from app.models.user import User
from app.schemas.sensor import DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _resolve_timeout(db: Session) -> int:
    s = db.query(Settings).first()
    return s.device_timeout if s else 30


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Device).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.get("/{device_id}/status")
def get_device_status(
    device_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return online/offline derived from last_seen vs device_timeout."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    timeout_sec = _resolve_timeout(db)
    if device.last_seen is None:
        computed_status = "offline"
    else:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=timeout_sec)
        computed_status = "online" if device.last_seen >= cutoff else "offline"

    return {
        "device_id": device.id,
        "device_code": device.device_code,
        "device_name": device.device_name,
        "status": computed_status,
        "last_seen": device.last_seen,
        "timeout_seconds": timeout_sec,
    }

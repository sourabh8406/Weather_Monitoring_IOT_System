"""Settings router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user
from app.database.connection import get_db
from app.models.settings import Settings
from app.models.user import User
from app.schemas.sensor import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session) -> Settings:
    s = db.query(Settings).first()
    if s is None:
        s = Settings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _get_or_create(db)


@router.put("", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    s = _get_or_create(db)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )
    for field, value in update_data.items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s

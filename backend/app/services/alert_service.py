"""Alert service — creates alerts when sensor readings breach thresholds."""

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity
from app.models.reading import SensorReading
from app.models.settings import Settings


def check_and_create_alerts(
    db: Session,
    reading: SensorReading,
    settings: Settings,
) -> None:
    """
    Compare *reading* values against *settings* thresholds.
    Insert an Alert row for every breach detected.
    """
    new_alerts: list[Alert] = []

    # --- Temperature ---
    if reading.temperature is not None:
        if reading.temperature >= settings.temperature_limit + 10:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="HIGH_TEMPERATURE",
                message=(
                    f"Critical temperature: {reading.temperature:.1f}°C "
                    f"(limit {settings.temperature_limit}°C)"
                ),
                severity=AlertSeverity.critical,
            ))
        elif reading.temperature >= settings.temperature_limit:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="HIGH_TEMPERATURE",
                message=(
                    f"High temperature: {reading.temperature:.1f}°C "
                    f"(limit {settings.temperature_limit}°C)"
                ),
                severity=AlertSeverity.warning,
            ))

    # --- Humidity ---
    if reading.humidity is not None:
        if reading.humidity >= settings.humidity_limit + 10:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="HIGH_HUMIDITY",
                message=(
                    f"Critical humidity: {reading.humidity:.1f}% "
                    f"(limit {settings.humidity_limit}%)"
                ),
                severity=AlertSeverity.critical,
            ))
        elif reading.humidity >= settings.humidity_limit:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="HIGH_HUMIDITY",
                message=(
                    f"High humidity: {reading.humidity:.1f}% "
                    f"(limit {settings.humidity_limit}%)"
                ),
                severity=AlertSeverity.warning,
            ))

    # --- Air Quality ---
    if reading.air_quality_raw is not None:
        if reading.air_quality_raw >= settings.air_quality_limit + 500:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="POOR_AIR_QUALITY",
                message=(
                    f"Critical air quality index: {reading.air_quality_raw} "
                    f"(limit {settings.air_quality_limit})"
                ),
                severity=AlertSeverity.critical,
            ))
        elif reading.air_quality_raw >= settings.air_quality_limit:
            new_alerts.append(Alert(
                device_id=reading.device_id,
                alert_type="POOR_AIR_QUALITY",
                message=(
                    f"Poor air quality index: {reading.air_quality_raw} "
                    f"(limit {settings.air_quality_limit})"
                ),
                severity=AlertSeverity.warning,
            ))

    # --- Rain ---
    if reading.rain_detected:
        new_alerts.append(Alert(
            device_id=reading.device_id,
            alert_type="RAIN_DETECTED",
            message="Rain detected by sensor.",
            severity=AlertSeverity.info,
        ))

    if new_alerts:
        db.add_all(new_alerts)
        db.flush()

-- ============================================================
-- Smart Weather Monitoring System — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS weather_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE weather_db;

-- ─────────────────────────────────────────────────────────────
-- users
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT           NOT NULL AUTO_INCREMENT,
    name          VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    role          ENUM('admin','user') NOT NULL DEFAULT 'user',
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- devices
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id          INT          NOT NULL AUTO_INCREMENT,
    device_name VARCHAR(100) NOT NULL,
    device_code VARCHAR(100) NOT NULL,
    location    VARCHAR(255),
    status      ENUM('online','offline') NOT NULL DEFAULT 'offline',
    last_seen   DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY uq_devices_code (device_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- sensor_readings
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
    id              BIGINT  NOT NULL AUTO_INCREMENT,
    device_id       INT     NOT NULL,
    temperature     FLOAT,
    humidity        FLOAT,
    pressure        FLOAT,
    rain_detected   BOOLEAN,
    air_quality_raw INT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_readings_device FOREIGN KEY (device_id)
        REFERENCES devices (id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_readings_device_time (device_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- alerts
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id         INT          NOT NULL AUTO_INCREMENT,
    device_id  INT          NOT NULL,
    alert_type VARCHAR(50)  NOT NULL,
    message    TEXT,
    severity   ENUM('critical','warning','info') NOT NULL,
    is_read    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_alerts_device FOREIGN KEY (device_id)
        REFERENCES devices (id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_alerts_device_read (device_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- settings
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS settings (
    id                INT   NOT NULL AUTO_INCREMENT,
    temperature_limit FLOAT NOT NULL DEFAULT 35.0,
    humidity_limit    FLOAT NOT NULL DEFAULT 80.0,
    air_quality_limit INT   NOT NULL DEFAULT 500,
    refresh_interval  INT   NOT NULL DEFAULT 5,
    device_timeout    INT   NOT NULL DEFAULT 30,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- Seed Data
-- ─────────────────────────────────────────────────────────────

-- Admin user (replace HASHED_PASSWORD with a real bcrypt hash in production)
INSERT INTO users (name, email, password_hash, role)
VALUES ('Admin User', 'admin@weathersystem.local', 'HASHED_PASSWORD', 'admin');

-- Default IoT device
INSERT INTO devices (device_name, device_code, location, status)
VALUES ('ESP32 Weather Station 01', 'ESP32_WEATHER_01', 'Roof - Building A', 'offline');

-- Default system settings
INSERT INTO settings (temperature_limit, humidity_limit, air_quality_limit, refresh_interval, device_timeout)
VALUES (35.0, 80.0, 500, 5, 30);

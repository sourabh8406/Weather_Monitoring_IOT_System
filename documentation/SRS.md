# Software Requirements Specification (SRS)
# Smart Weather Monitoring System

**Document Version:** 1.0  
**Date:** 2024  
**Status:** Approved

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for the **Smart Weather Monitoring System**, an IoT application that collects environmental sensor data from an ESP32-based device, persists it in a MySQL database via a Python FastAPI backend, and presents it through a responsive web dashboard.

### 1.2 Scope

The system comprises three tiers:

1. **IoT Edge** — ESP32 microcontroller with DHT22, BMP280, rain sensor, and MQ-135
2. **Backend** — Python FastAPI REST API + MySQL 8.0 database
3. **Frontend** — HTML/CSS/JS single-page dashboard

The system is intended for indoor or outdoor deployment as a personal or small-facility weather station.

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| ESP32 | Espressif ESP32 dual-core 240 MHz WiFi microcontroller |
| JWT | JSON Web Token — stateless authentication token (RFC 7519) |
| hPa | Hectopascal — unit of barometric pressure (1 hPa = 1 mbar) |
| ORM | Object-Relational Mapping — SQLAlchemy in this project |
| SRS | Software Requirements Specification |

---

## 2. Functional Requirements

| ID | Requirement | Priority |
|----|------------|---------|
| FR-01 | The ESP32 firmware SHALL read temperature and humidity from a DHT22 sensor at the configured interval | High |
| FR-02 | The ESP32 firmware SHALL read barometric pressure from a BMP280 sensor via I2C | High |
| FR-03 | The ESP32 firmware SHALL read rain presence (analog + digital) from a rain sensor module | High |
| FR-04 | The ESP32 firmware SHALL read raw air quality ADC value from an MQ-135 sensor | High |
| FR-05 | The ESP32 firmware SHALL validate all readings against physical bounds before transmitting | High |
| FR-06 | The ESP32 firmware SHALL transmit a JSON payload to the backend via HTTP POST over WiFi at every interval | High |
| FR-07 | The backend SHALL accept sensor readings from any registered device without requiring authentication | High |
| FR-08 | The backend SHALL persist each validated reading to the `sensor_readings` table and update `devices.last_seen` | High |
| FR-09 | The backend SHALL automatically create alerts when any reading exceeds the configured threshold stored in `settings` | High |
| FR-10 | The backend SHALL provide JWT-based authentication; users receive a token on login and present it as a Bearer token for protected routes | High |
| FR-11 | The backend SHALL enforce role-based access: only users with `role='admin'` may update system settings | High |
| FR-12 | The backend SHALL expose historical sensor data filterable by date range and limit | Medium |
| FR-13 | The frontend dashboard SHALL display the latest sensor readings and auto-refresh at the configured interval | High |
| FR-14 | The frontend SHALL allow authenticated users to view, filter, and mark alerts as read | Medium |

---

## 3. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|------------|
| NFR-01 | Performance | GET /api/sensors/latest SHALL respond in < 200 ms (p95) under 20 concurrent users |
| NFR-02 | Performance | GET /api/sensors/history (limit=100) SHALL respond in < 500 ms (p95) |
| NFR-03 | Scalability | The database schema SHALL support multiple devices with no structural changes |
| NFR-04 | Security | Passwords SHALL be hashed using bcrypt with a minimum cost factor of 12 |
| NFR-05 | Security | JWT tokens SHALL expire after 1 440 minutes (24 hours) |
| NFR-06 | Security | The SECRET_KEY used for JWT signing SHALL be stored in an environment variable, never in source code |
| NFR-07 | Reliability | The ESP32 firmware SHALL attempt WiFi reconnection before each send cycle |
| NFR-08 | Usability | The web dashboard SHALL be responsive and usable on screens ≥ 375 px wide |
| NFR-09 | Maintainability | Backend source code SHALL follow PEP 8 style and be organised into distinct modules (api, services, models, schemas, core) |
| NFR-10 | Portability | The backend SHALL run on Python 3.10+ on Windows, macOS, and Linux |
| NFR-11 | Observability | The ESP32 firmware SHALL output structured debug messages to Serial at 115200 baud |
| NFR-12 | Data Retention | The `sensor_readings` table SHALL support at least 10 million rows with query performance maintained by composite index on `(device_id, created_at)` |

---

## 4. Database Schema

### 4.1 `users`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Unique user identifier |
| `name` | VARCHAR(100) | NOT NULL | Full name |
| `email` | VARCHAR(150) | NOT NULL, UNIQUE | Login email |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `role` | ENUM('admin','user') | DEFAULT 'user' | Access role |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Registration time |

### 4.2 `devices`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Unique device identifier |
| `device_name` | VARCHAR(100) | NOT NULL | Human-readable name |
| `device_code` | VARCHAR(100) | NOT NULL, UNIQUE | Firmware identifier (e.g. `ESP32_WEATHER_01`) |
| `location` | VARCHAR(255) | — | Physical location description |
| `status` | ENUM('online','offline') | DEFAULT 'offline' | Derived from `last_seen` |
| `last_seen` | DATETIME | — | Timestamp of last successful reading |

### 4.3 `sensor_readings`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | BIGINT | PK, AUTO_INCREMENT | Unique reading identifier |
| `device_id` | INT | FK → `devices.id` | Source device |
| `temperature` | FLOAT | — | °C (-40 to 85) |
| `humidity` | FLOAT | — | %RH (0 to 100) |
| `pressure` | FLOAT | — | hPa (300 to 1100) |
| `rain_detected` | BOOLEAN | — | TRUE if rain present |
| `air_quality_raw` | INT | — | ADC value (0 to 4095) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Insertion time |

**Indexes:** `idx_sensor_device_time (device_id, created_at)`

### 4.4 `alerts`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Unique alert identifier |
| `device_id` | INT | FK → `devices.id` | Source device |
| `alert_type` | VARCHAR(50) | NOT NULL | e.g. `temperature_high` |
| `message` | TEXT | — | Human-readable description |
| `severity` | ENUM('critical','warning','info') | NOT NULL | Alert severity level |
| `is_read` | BOOLEAN | DEFAULT FALSE | Whether the alert has been acknowledged |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Alert generation time |

**Indexes:** `idx_alert_device_read (device_id, is_read)`

### 4.5 `settings`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | INT | PK, AUTO_INCREMENT | Singleton row (always id=1) |
| `temperature_limit` | FLOAT | DEFAULT 35.0 | Alert threshold °C |
| `humidity_limit` | FLOAT | DEFAULT 80.0 | Alert threshold %RH |
| `air_quality_limit` | INT | DEFAULT 500 | Alert threshold ADC value |
| `refresh_interval` | INT | DEFAULT 5 | Dashboard refresh seconds |
| `device_timeout` | INT | DEFAULT 30 | Seconds before device marked offline |
| `updated_at` | DATETIME | DEFAULT ... ON UPDATE | Last modified time |

---

## 5. API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | None | Register a new user account |
| `POST` | `/api/auth/login` | None | Authenticate and receive a JWT |
| `GET` | `/api/auth/me` | Bearer | Return the authenticated user's profile |
| `POST` | `/api/sensors/readings` | None | Submit sensor data from ESP32 |
| `GET` | `/api/sensors/latest` | Bearer | Retrieve the most recent reading per device |
| `GET` | `/api/sensors/history` | Bearer | Query readings by date range (`start_date`, `end_date`, `limit`) |
| `GET` | `/api/sensors/status` | Bearer | Return online/offline status for all devices |
| `GET` | `/api/devices` | Bearer | List all registered devices |
| `GET` | `/api/devices/{id}` | Bearer | Retrieve a specific device by ID |
| `GET` | `/api/devices/{id}/status` | Bearer | Online/offline status of a single device |
| `GET` | `/api/alerts` | Bearer | Retrieve all alerts |
| `GET` | `/api/alerts/active` | Bearer | Retrieve only unread alerts |
| `PATCH` | `/api/alerts/{id}/read` | Bearer | Mark a specific alert as read |
| `GET` | `/api/settings` | Bearer | Retrieve current system settings |
| `PUT` | `/api/settings` | Admin | Update system threshold and interval settings |

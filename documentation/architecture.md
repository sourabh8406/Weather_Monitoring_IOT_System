# System Architecture — Smart Weather Monitoring System

**Version:** 1.0  
**Date:** 2024  
**Status:** Current

---

## 1. Overview

The Smart Weather Monitoring System is a three-tier IoT application that continuously collects environmental sensor data, persists it to a relational database, and presents live and historical visualisations through a web dashboard. The design follows a clean separation of concerns — hardware, backend, and frontend — allowing each layer to be developed, tested, and scaled independently.

---

## 2. Three-Tier Architecture

### 2.1 Tier 1 — IoT / Edge Layer

| Component | Technology | Role |
|-----------|-----------|------|
| Microcontroller | ESP32 (Xtensa LX6 dual-core 240 MHz) | Sensor orchestration, WiFi connectivity |
| Temperature & Humidity | DHT22 | Reads ambient conditions every cycle |
| Pressure | BMP280 (I2C) | Reads barometric pressure |
| Rain Detection | FC-37 module | Analog + digital rain presence |
| Air Quality | MQ-135 | Raw gas concentration ADC reading |
| Communication | HTTP POST over WiFi (802.11 b/g/n) | Sends JSON payload to backend |

The firmware reads all sensors in each loop iteration, validates values against physical bounds, serialises the payload to JSON, and POSTs it to the backend API. If WiFi drops, the firmware reconnects before the next send attempt. The configurable `SEND_INTERVAL` (default 5 000 ms) controls the sampling rate.

### 2.2 Tier 2 — Application / Backend Layer

| Component | Technology | Role |
|-----------|-----------|------|
| Web Framework | Python FastAPI | REST API, request routing, validation |
| ORM | SQLAlchemy 2.x | Database abstraction |
| Database | MySQL 8.0 | Persistent storage |
| Auth | python-jose (JWT) + passlib (bcrypt) | Stateless authentication |
| Schema Validation | Pydantic v2 | Request/response models |
| ASGI Server | Uvicorn | Production-ready async server |

The backend exposes a REST API consumed by both the ESP32 (write-only, no auth) and the web dashboard (read/write, JWT). Business logic is in service modules (`sensor_service`, `alert_service`) decoupled from route handlers.

### 2.3 Tier 3 — Presentation / Frontend Layer

| Component | Technology | Role |
|-----------|-----------|------|
| Markup | HTML5 | Page structure |
| Styling | Tailwind CSS (CDN) | Responsive utility-first layout |
| Charts | Chart.js | Live and historical line/bar charts |
| API client | Fetch API (vanilla JS) | Async data retrieval |
| Auth | JWT stored in `localStorage` | Per-request Authorization header |

The dashboard auto-refreshes current readings at the configured interval and allows users to query historical data by date range.

---

## 3. Data Flow — Sensor Reading Lifecycle

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. ESP32 reads all sensors (DHT22, BMP280, Rain, MQ-135)            │
│  2. Validates readings against physical bounds                        │
│  3. Serialises to JSON:                                               │
│     { "device_code":"ESP32_WEATHER_01",                               │
│       "temperature":27.3, "humidity":61.2,                           │
│       "pressure":1012.5, "rain_detected":false,                       │
│       "air_quality_raw":420 }                                         │
│  4. HTTP POST  →  /api/sensors/readings                               │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  5. FastAPI route handler receives request (no auth required)         │
│  6. Pydantic SensorReadingCreate validates field types & presence     │
│  7. sensor_service.save_reading():                                    │
│     a. Look up device by device_code                                  │
│     b. Update device.last_seen = NOW()                                │
│     c. INSERT into sensor_readings                                    │
│     d. Retrieve current settings thresholds                           │
│     e. alert_service.check_and_create_alerts()                        │
│        — If temperature > settings.temperature_limit → alert (warning)│
│        — If humidity > settings.humidity_limit → alert (warning)      │
│        — If air_quality_raw > settings.air_quality_limit → alert      │
│     f. Return 201 Created with saved reading                          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  8. Frontend polls GET /api/sensors/latest  (every N seconds)         │
│  9. Renders gauges, tiles, and live chart update                      │
│  10. User may query GET /api/sensors/history?start_date=&end_date=   │
│  11. Alerts visible in /api/alerts/active; user marks them read      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database ER Diagram

```
┌─────────────────────────┐         ┌──────────────────────────────────┐
│         users           │         │             devices               │
├─────────────────────────┤         ├──────────────────────────────────┤
│ PK  id          INT     │         │ PK  id            INT            │
│     name        VARCHAR │         │     device_name   VARCHAR(100)   │
│     email       VARCHAR │◄──┐     │     device_code   VARCHAR(100)   │
│     password_hash       │   │     │     location      VARCHAR(255)   │
│     role        ENUM    │   │     │     status        ENUM           │
│     created_at  DATETIME│   │     │     last_seen     DATETIME       │
└─────────────────────────┘   │     └──────────────┬───────────────────┘
                              │                    │  1
                              │                    │
                              │            ┌───────┴─────────────────────┐
                              │      ┌────►│       sensor_readings        │
                              │      │     ├─────────────────────────────┤
                              │      │     │ PK  id              BIGINT  │
                              │      │  FK │     device_id        INT    │
                              │      │     │     temperature      FLOAT  │
                              │      │     │     humidity         FLOAT  │
                              │      │     │     pressure         FLOAT  │
                              │      │     │     rain_detected    BOOL   │
                              │      │     │     air_quality_raw  INT    │
                              │      │     │     created_at       DATETIME│
                              │      │     └─────────────────────────────┘
                              │      │
                              │      │  ┌──────────────────────────────┐
                              │      └─►│           alerts              │
                              │         ├──────────────────────────────┤
                              │      FK │ PK  id           INT         │
                              │         │     device_id     INT        │
                              │         │     alert_type    VARCHAR    │
                              │         │     message       TEXT       │
                              │         │     severity      ENUM       │
                              │         │     is_read       BOOLEAN    │
                              │         │     created_at    DATETIME   │
                              │         └──────────────────────────────┘
                              │
                              │   ┌───────────────────────────────────┐
                              │   │            settings                │
                              │   ├───────────────────────────────────┤
                              │   │ PK  id                  INT       │
                              │   │     temperature_limit   FLOAT     │
                              │   │     humidity_limit      FLOAT     │
                              │   │     air_quality_limit   INT       │
                              │   │     refresh_interval    INT       │
                              │   │     device_timeout      INT       │
                              │   │     updated_at          DATETIME  │
                              │   └───────────────────────────────────┘
```

**Relationships:**
- `devices` **1 → N** `sensor_readings` (FK: `sensor_readings.device_id → devices.id`)
- `devices` **1 → N** `alerts` (FK: `alerts.device_id → devices.id`)
- `users` is standalone (no FK to readings/alerts in v1; role-based access controlled by JWT claims)
- `settings` is a singleton table (one row controls global thresholds)

---

## 5. API Endpoint Reference

| Method | Path | Auth | Description | Request Body | Response |
|--------|------|------|-------------|-------------|---------|
| `POST` | `/api/auth/register` | None | Register user | `{name, email, password}` | `UserResponse` |
| `POST` | `/api/auth/login` | None | Login | `{email, password}` | `{access_token, token_type}` |
| `GET` | `/api/auth/me` | Bearer | Current user | — | `UserResponse` |
| `POST` | `/api/sensors/readings` | None | Submit reading | `SensorReadingCreate` | `SensorReadingResponse` |
| `GET` | `/api/sensors/latest` | Bearer | Latest per device | — | `List[SensorLatest]` |
| `GET` | `/api/sensors/history` | Bearer | Historical | `?start_date&end_date&limit` | `List[SensorReadingResponse]` |
| `GET` | `/api/sensors/status` | Bearer | All device statuses | — | `List[DeviceResponse]` |
| `GET` | `/api/devices` | Bearer | List devices | — | `List[DeviceResponse]` |
| `GET` | `/api/devices/{id}` | Bearer | Device detail | — | `DeviceResponse` |
| `GET` | `/api/devices/{id}/status` | Bearer | Device online status | — | `DeviceResponse` |
| `GET` | `/api/alerts` | Bearer | All alerts | — | `List[AlertResponse]` |
| `GET` | `/api/alerts/active` | Bearer | Unread alerts | — | `List[AlertResponse]` |
| `PATCH` | `/api/alerts/{id}/read` | Bearer | Mark read | — | `AlertResponse` |
| `GET` | `/api/settings` | Bearer | Get settings | — | `SettingsResponse` |
| `PUT` | `/api/settings` | Admin | Update settings | `SettingsUpdate` | `SettingsResponse` |

---

## 6. Security Architecture

### 6.1 Authentication Flow (JWT)

```
Client                        FastAPI                        MySQL
  │                              │                              │
  │  POST /api/auth/login        │                              │
  │  {email, password}           │                              │
  │─────────────────────────────►│                              │
  │                              │  SELECT user WHERE email=?   │
  │                              │─────────────────────────────►│
  │                              │  ◄── user record ───────────│
  │                              │                              │
  │                              │  passlib.verify(password,    │
  │                              │    user.password_hash)       │
  │                              │                              │
  │                              │  jose.encode({sub, role,     │
  │                              │    exp=now+1440min})         │
  │                              │                              │
  │  ◄── {access_token, type} ──│                              │
  │                              │                              │
  │  GET /api/sensors/latest     │                              │
  │  Authorization: Bearer <tok> │                              │
  │─────────────────────────────►│                              │
  │                              │  jose.decode(token, SECRET)  │
  │                              │  → extract sub, role         │
  │                              │  → fetch user from DB        │
  │                              │                              │
  │  ◄── 200 JSON ──────────────│                              │
```

### 6.2 Password Hashing

- Algorithm: **bcrypt** via `passlib[bcrypt]`
- Cost factor: default 12 rounds
- Passwords are never stored in plaintext; only the bcrypt hash is persisted

### 6.3 Role-Based Access

| Role | Permissions |
|------|------------|
| `user` | Read all data, mark alerts read |
| `admin` | All user permissions + update settings |

The `get_admin_user` dependency raises `HTTP 403` if the authenticated user's role is not `admin`.

### 6.4 ESP32 Endpoint (No Auth)

`POST /api/sensors/readings` is intentionally unauthenticated to simplify firmware. In production, consider adding a device API key header validated server-side.

---

## 7. Deployment Notes

### 7.1 Development

```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
python -m http.server 3000 --directory frontend

# Database
mysql -u root -p weather_db < database/schema.sql
```

CORS is set to `allow_origins=["*"]` for local development. All traffic is plain HTTP.

### 7.2 Production Recommendations

| Concern | Recommendation |
|---------|---------------|
| HTTPS | Terminate TLS at Nginx reverse proxy; use Let's Encrypt |
| CORS | Restrict `allow_origins` to the production domain |
| Secret key | Generate 64-byte random hex: `openssl rand -hex 32` |
| Database | Use a dedicated MySQL user with least-privilege grants |
| Uvicorn | Run behind Gunicorn with multiple workers |
| ESP32 | Use HTTPS and add a pre-shared API key header |
| Environment | Store `.env` outside the repository; use secrets manager in cloud |
| Backups | Schedule daily `mysqldump` of `weather_db` |

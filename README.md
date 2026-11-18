# Smart Weather Monitoring System 🌤️

![Python](https://img.shields.io/badge/Python-FastAPI-009688?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479A1?logo=mysql&logoColor=white)
![ESP32](https://img.shields.io/badge/Hardware-ESP32-E7352C?logo=espressif&logoColor=white)
![Chart.js](https://img.shields.io/badge/Charts-Chart.js-FF6384?logo=chartdotjs&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen)

## Overview

A full-stack IoT weather monitoring system that collects real-time environmental data from an ESP32 microcontroller fitted with temperature, humidity, pressure, rain, and air-quality sensors. Data is transmitted over WiFi to a Python FastAPI backend, persisted in MySQL, and visualised in a responsive web dashboard with live charts and threshold-based alerts.

> For the verified local setup steps, environment variables, and first admin account setup, see [documentation/setup.md](documentation/setup.md).

---

## Features

- 📡 **Real-time sensor data** — temperature, humidity, barometric pressure, rain detection, and air quality (MQ-135)
- 📊 **Historical charts** — interactive Chart.js graphs with configurable time ranges
- 🔔 **Threshold alerts** — automatic critical/warning/info alerts when readings exceed configurable limits
- 🔐 **JWT authentication** — role-based access (admin / user) with secure login
- 🖥️ **Responsive dashboard** — Tailwind CSS UI that works on desktop, tablet and mobile
- 🌐 **REST API** — well-documented FastAPI endpoints with auto-generated Swagger docs at `/docs`
- ⚙️ **Configurable settings** — adjust thresholds and polling intervals without redeploying
- 🏭 **Multi-device ready** — schema supports multiple named ESP32 devices
- 🛑 **Device online/offline status** — heartbeat detection based on `last_seen` timestamp

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         IoT LAYER                               │
│                                                                 │
│  [DHT22]  [BMP280]  [Rain Sensor]  [MQ-135]                    │
│      └──────────┬──────────┘            │                       │
│                 ▼                       ▼                       │
│            ┌─────────┐                                          │
│            │  ESP32  │  (Arduino firmware)                      │
│            └────┬────┘                                          │
└─────────────────┼───────────────────────────────────────────────┘
                  │  HTTP POST  (JSON payload over WiFi)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER                             │
│                                                                 │
│           ┌──────────────────────────┐                         │
│           │  Python FastAPI (port 8000) │                       │
│           │  • /api/sensors/readings  │                         │
│           │  • /api/auth/*            │                         │
│           │  • /api/alerts/*          │                         │
│           │  • /api/settings/*        │                         │
│           └────────────┬─────────────┘                         │
│                        │  SQLAlchemy ORM                        │
│                        ▼                                        │
│               ┌─────────────────┐                              │
│               │   MySQL 8.0     │                               │
│               │  weather_db     │                               │
│               └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                  │  REST API (JSON)
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                             │
│                                                                 │
│        ┌────────────────────────────────────────┐              │
│        │  HTML + Tailwind CSS + Chart.js         │              │
│        │  • Live dashboard with auto-refresh     │              │
│        │  • Historical trend charts              │              │
│        │  • Alert management panel               │              │
│        └────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware Requirements

| Component | Model / Spec | Purpose |
|-----------|-------------|---------|
| Microcontroller | ESP32 (Dev Kit v1 or similar) | WiFi-enabled controller |
| Temperature & Humidity | DHT22 (AM2302) | ±0.5 °C, ±2–5 %RH |
| Barometric Pressure | BMP280 | 300–1100 hPa, I2C |
| Rain Sensor Module | FC-37 or YL-83 | Analog + digital rain detection |
| Air Quality Sensor | MQ-135 | NH₃, CO₂, alcohol, smoke (analog) |
| Passive components | 10 kΩ resistor (DHT22 pull-up) | Signal integrity |
| Wiring | Jumper wires (M-M, M-F) | Connections |
| Power | USB 5 V / micro-USB or 3.3 V regulated | ESP32 power |
| Prototyping | Breadboard | Assembly |

---

## Wiring Guide

### DHT22 — Temperature & Humidity Sensor

| Sensor Pin | ESP32 Pin | Notes |
|-----------|-----------|-------|
| VCC | 3.3 V | Do NOT use 5 V |
| GND | GND | — |
| DATA | GPIO 4 | Add 10 kΩ pull-up to 3.3 V |

### BMP280 — Barometric Pressure Sensor (I2C)

| Sensor Pin | ESP32 Pin | Notes |
|-----------|-----------|-------|
| VCC | 3.3 V | — |
| GND | GND | — |
| SDA | GPIO 21 | I2C data |
| SCL | GPIO 22 | I2C clock |
| SDO | GND | Sets I2C address 0x76 |

### Rain Sensor Module

| Sensor Pin | ESP32 Pin | Notes |
|-----------|-----------|-------|
| VCC | 3.3 V | — |
| GND | GND | — |
| D0 (digital) | GPIO 27 | LOW = rain detected |
| A0 (analog) | GPIO 34 | 0–4095 ADC range |

### MQ-135 — Air Quality Sensor

| Sensor Pin | ESP32 Pin | Notes |
|-----------|-----------|-------|
| VCC | 5 V | Requires 5 V heater |
| GND | GND | — |
| A0 (analog) | GPIO 35 | 0–4095 ADC range |

> ⚠️ **MQ-135 Warm-up**: Allow 24–48 hours of continuous power for accurate baseline calibration.

---

## Software Requirements

| Component | Version |
|-----------|---------|
| Python | 3.10+ |
| MySQL | 8.0+ |
| Arduino IDE | 2.x |
| ESP32 Board Package | ≥ 2.0 (via Boards Manager) |

### Arduino Libraries (install via Library Manager)

| Library | Author | Version |
|---------|--------|---------|
| DHT sensor library | Adafruit | ≥ 1.4.4 |
| Adafruit BMP280 Library | Adafruit | ≥ 2.6.6 |
| ArduinoJson | Benoit Blanc | ≥ 6.21 |

---

## Installation & Setup

### 1. Database Setup

```sql
CREATE DATABASE weather_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE weather_db;
SOURCE database/schema.sql;
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS / Linux

pip install -r requirements.txt

cp .env.example .env
# Open .env and fill in your database credentials and a random SECRET_KEY

uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 3. ESP32 Setup

1. Open **Arduino IDE 2.x**
2. Go to **File → Preferences → Additional Board Manager URLs** and add:  
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install **esp32** board package via **Boards Manager**
4. Install the three libraries listed above via **Library Manager**
5. Open `esp32/weather_monitor.ino`
6. Edit the **CONFIGURATION** section at the top:
   - `ssid` — your WiFi network name
   - `password` — your WiFi password
   - `serverURL` — your machine's local IP, e.g. `http://192.168.1.100:8000/api/sensors/readings`
7. Select your board: **Tools → Board → ESP32 → ESP32 Dev Module**
8. Select the correct COM port and click **Upload**
9. Open **Serial Monitor** at 115200 baud to watch debug output

### 4. Frontend

```bash
# Option A — open directly in browser
start frontend/index.html   # Windows
open frontend/index.html    # macOS

# Option B — serve with Python (required for fetch() on some browsers)
python -m http.server 3000 --directory frontend
# Then open http://localhost:3000
```

---

## API Documentation

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | None | Register new user |
| `POST` | `/api/auth/login` | None | Login, receive JWT |
| `GET` | `/api/auth/me` | Bearer | Get current user profile |
| `POST` | `/api/sensors/readings` | None | Submit sensor reading (ESP32) |
| `GET` | `/api/sensors/latest` | Bearer | Get latest readings per device |
| `GET` | `/api/sensors/history` | Bearer | Get historical readings (`?start_date&end_date&limit`) |
| `GET` | `/api/sensors/status` | Bearer | Device online/offline status |
| `GET` | `/api/devices` | Bearer | List all devices |
| `GET` | `/api/devices/{id}` | Bearer | Get device detail |
| `GET` | `/api/devices/{id}/status` | Bearer | Single device status |
| `GET` | `/api/alerts` | Bearer | List all alerts |
| `GET` | `/api/alerts/active` | Bearer | List unread alerts |
| `PATCH` | `/api/alerts/{id}/read` | Bearer | Mark alert as read |
| `GET` | `/api/settings` | Bearer | Get current settings |
| `PUT` | `/api/settings` | Admin | Update settings |

---

## Default Credentials

After running `database/schema.sql` a seed admin user is created:

- **Email:** `admin@weather.local`
- **Password:** Generate a bcrypt hash and update the `users` table, or run:

```bash
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print(ctx.hash('YourPassword123!'))"
# Then UPDATE users SET password_hash='<output>' WHERE email='admin@weather.local';
```

---

## Project Structure

```
smart-weather-monitoring/
├── esp32/
│   └── weather_monitor.ino       # Arduino firmware
├── database/
│   └── schema.sql                # MySQL schema + seed data
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py               # FastAPI application entry point
│       ├── database/
│       │   └── connection.py     # SQLAlchemy engine & session
│       ├── models/               # ORM models
│       │   ├── user.py
│       │   ├── device.py
│       │   ├── reading.py
│       │   ├── alert.py
│       │   └── settings.py
│       ├── schemas/              # Pydantic v2 schemas
│       │   ├── user.py
│       │   └── sensor.py
│       ├── core/
│       │   ├── config.py         # App settings
│       │   └── security.py       # JWT + password hashing
│       ├── services/
│       │   ├── sensor_service.py
│       │   └── alert_service.py
│       └── api/
│           ├── auth.py
│           ├── sensors.py
│           ├── devices.py
│           ├── alerts.py
│           └── settings.py
├── frontend/
│   ├── index.html                # Dashboard SPA
│   ├── login.html
│   └── assets/
│       ├── css/
│       └── js/
└── documentation/
    ├── SRS.md
    ├── architecture.md
    └── testing.md
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Smart Weather Monitoring Project Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

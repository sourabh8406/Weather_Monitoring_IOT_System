# Testing Documentation — Smart Weather Monitoring System

**Version:** 1.0  
**Date:** 2024

---

## 1. Backend Unit Test Cases

### 1.1 Security Module

| Test ID | Component | Input | Expected Output |
|---------|-----------|-------|----------------|
| UT-SEC-01 | `hash_password` | `"password123"` | Returns 60-char bcrypt hash starting with `$2b$` |
| UT-SEC-02 | `verify_password` | plain=`"password123"`, hash=correct | Returns `True` |
| UT-SEC-03 | `verify_password` | plain=`"wrongpass"`, hash=correct | Returns `False` |
| UT-SEC-04 | `create_access_token` | `{sub:"1", role:"user"}` | Returns non-empty JWT string |
| UT-SEC-05 | `decode_token` | Valid JWT | Returns `TokenData` with correct `sub` |
| UT-SEC-06 | `decode_token` | Expired JWT | Raises `JWTError` |
| UT-SEC-07 | `decode_token` | Malformed string | Raises `JWTError` |

### 1.2 Sensor Validation (sensor_service)

| Test ID | Component | Input | Expected Output |
|---------|-----------|-------|----------------|
| UT-SVC-01 | `save_reading` | temperature=`27.3`, all others valid | Record saved, returns `SensorReadingResponse` |
| UT-SVC-02 | `save_reading` | temperature=`-50` (below -40) | Raises `HTTP 422` / validation error |
| UT-SVC-03 | `save_reading` | temperature=`90` (above 85) | Raises `HTTP 422` |
| UT-SVC-04 | `save_reading` | humidity=`105` (above 100) | Raises `HTTP 422` |
| UT-SVC-05 | `save_reading` | pressure=`250` (below 300) | Raises `HTTP 422` |
| UT-SVC-06 | `save_reading` | air_quality_raw=`5000` (above 4095) | Raises `HTTP 422` |
| UT-SVC-07 | `save_reading` | Unknown `device_code` | Raises `HTTP 404` |

### 1.3 Alert Service

| Test ID | Component | Input | Expected Output |
|---------|-----------|-------|----------------|
| UT-ALT-01 | `check_and_create_alerts` | temperature=`36`, limit=`35` | Alert created with severity `warning` |
| UT-ALT-02 | `check_and_create_alerts` | temperature=`30`, limit=`35` | No alert created |
| UT-ALT-03 | `check_and_create_alerts` | humidity=`85`, limit=`80` | Alert created with severity `warning` |
| UT-ALT-04 | `check_and_create_alerts` | air_quality_raw=`600`, limit=`500` | Alert created with severity `warning` |
| UT-ALT-05 | `check_and_create_alerts` | All readings within limits | Zero new alerts |

### 1.4 Config / Settings

| Test ID | Component | Input | Expected Output |
|---------|-----------|-------|----------------|
| UT-CFG-01 | `Settings` (pydantic-settings) | Valid `.env` file | Loads `DATABASE_URL`, `SECRET_KEY`, etc. |
| UT-CFG-02 | `Settings` | Missing `SECRET_KEY` | Raises `ValidationError` |

---

## 2. API Test Cases (curl Examples)

### 2.1 Authentication

**Register a new user**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"Test1234!"}'
```
*Expected:* `201 Created` with `UserResponse` JSON

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```
*Expected:* `200 OK` with `{"access_token":"<jwt>","token_type":"bearer"}`

**Get current user (save token from login)**
```bash
export TOKEN="<paste_access_token_here>"
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
*Expected:* `200 OK` with `UserResponse`

**Unauthenticated request**
```bash
curl -X GET http://localhost:8000/api/auth/me
```
*Expected:* `401 Unauthorized`

---

### 2.2 Sensor Readings

**Submit a reading (ESP32 style, no auth)**
```bash
curl -X POST http://localhost:8000/api/sensors/readings \
  -H "Content-Type: application/json" \
  -d '{
    "device_code": "ESP32_WEATHER_01",
    "temperature": 27.3,
    "humidity": 61.5,
    "pressure": 1012.4,
    "rain_detected": false,
    "air_quality_raw": 420
  }'
```
*Expected:* `201 Created`

**Submit with out-of-range temperature**
```bash
curl -X POST http://localhost:8000/api/sensors/readings \
  -H "Content-Type: application/json" \
  -d '{"device_code":"ESP32_WEATHER_01","temperature":999,"humidity":50,"pressure":1013,"rain_detected":false,"air_quality_raw":300}'
```
*Expected:* `422 Unprocessable Entity`

**Get latest readings**
```bash
curl -X GET http://localhost:8000/api/sensors/latest \
  -H "Authorization: Bearer $TOKEN"
```
*Expected:* `200 OK` with array of latest readings per device

**Get historical data**
```bash
curl -X GET "http://localhost:8000/api/sensors/history?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```
*Expected:* `200 OK` with array of readings ordered by `created_at` DESC

---

### 2.3 Alerts

**Get all alerts**
```bash
curl -X GET http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN"
```

**Get active (unread) alerts**
```bash
curl -X GET http://localhost:8000/api/alerts/active \
  -H "Authorization: Bearer $TOKEN"
```

**Mark alert as read**
```bash
curl -X PATCH http://localhost:8000/api/alerts/1/read \
  -H "Authorization: Bearer $TOKEN"
```
*Expected:* `200 OK` with updated `AlertResponse` where `is_read=true`

---

### 2.4 Devices

**List all devices**
```bash
curl -X GET http://localhost:8000/api/devices \
  -H "Authorization: Bearer $TOKEN"
```

**Get device by ID**
```bash
curl -X GET http://localhost:8000/api/devices/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Get device status (online/offline)**
```bash
curl -X GET http://localhost:8000/api/devices/1/status \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2.5 Settings

**Get settings**
```bash
curl -X GET http://localhost:8000/api/settings \
  -H "Authorization: Bearer $TOKEN"
```

**Update settings (admin only)**
```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature_limit":38.0,"humidity_limit":85.0,"air_quality_limit":600}'
```
*Expected:* `200 OK` with updated `SettingsResponse`

**Update settings as non-admin**
```bash
curl -X PUT http://localhost:8000/api/settings \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"temperature_limit":38.0}'
```
*Expected:* `403 Forbidden`

---

## 3. Hardware Test Procedure

Verify each sensor individually before full system integration.

### 3.1 DHT22 — Temperature & Humidity

1. Upload a minimal sketch: `Serial.println(dht.readTemperature());`
2. Open Serial Monitor at 115200 baud
3. **Pass criteria:** Value is numeric, in range –40 to 80 °C, stable (< ±1 °C across 10 readings)
4. Breathe on sensor — humidity should increase noticeably
5. **Fail:** `nan`, constant 0, or out-of-range value → check wiring, 10 kΩ pull-up, power

### 3.2 BMP280 — Barometric Pressure

1. Upload I2C scanner sketch; verify address `0x76` or `0x77` appears
2. Upload minimal sketch: `Serial.println(bmp.readPressure() / 100.0F);`
3. **Pass criteria:** Value between 950–1050 hPa at sea level (adjust for altitude)
4. **Fail:** 0 or `nan` → check SDA/SCL wiring, I2C address, power (3.3 V)

### 3.3 Rain Sensor Module

1. Upload sketch reading `analogRead(34)` and `digitalRead(27)`
2. **Dry state:** analog ≈ 4095 (or high), digital = HIGH
3. **Wet state:** drip water on sensor pad; analog drops, digital goes LOW
4. **Pass criteria:** clear transition between dry/wet for both channels
5. **Fail:** digital never changes → check comparator potentiometer on module

### 3.4 MQ-135 — Air Quality

1. Upload sketch reading `analogRead(35)`
2. Power on and wait at least 5 minutes for heater warm-up
3. **Cold/fresh air:** ADC value typically 100–400 (varies by unit and temperature)
4. **Near gas source:** value should increase noticeably
5. **Pass criteria:** value responds to gas exposure; stable baseline after warm-up
6. ⚠️ **Note:** Full accuracy requires 24–48 h continuous power

### 3.5 Full ESP32 WiFi Connection Test

1. Set `ssid`, `password`, `serverURL` in firmware
2. Upload and open Serial Monitor
3. **Pass criteria:** IP address printed, then each loop shows valid readings + `HTTP 201`
4. **Fail:** "Failed to connect" → check credentials, signal strength, server address

---

## 4. Integration Test Checklist

| # | Test | Expected Result | ✓ |
|---|------|----------------|---|
| IT-01 | ESP32 POSTs reading → check MySQL `sensor_readings` table | Row inserted within SEND_INTERVAL | ☐ |
| IT-02 | POST reading with valid device_code → `devices.last_seen` updated | Timestamp ≤ 5 s old | ☐ |
| IT-03 | POST reading with temperature > limit → alert row created | Alert in `alerts` table with `is_read=false` | ☐ |
| IT-04 | Frontend GET `/api/sensors/latest` returns new reading | Matches most recent DB row | ☐ |
| IT-05 | Frontend marks alert read via PATCH → DB updated | `is_read=true` in DB | ☐ |
| IT-06 | Disconnect ESP32 for `device_timeout` seconds → status shows offline | `status=offline` from `/api/sensors/status` | ☐ |
| IT-07 | Reconnect ESP32 → status returns online | `status=online`, `last_seen` refreshed | ☐ |
| IT-08 | Admin updates settings via PUT → next alert uses new threshold | Alert triggered at new limit | ☐ |
| IT-09 | Non-admin PUT /api/settings → 403 | 403 response | ☐ |
| IT-10 | Invalid JWT → all protected endpoints return 401 | 401 response | ☐ |

---

## 5. UI Test Checklist

### 5.1 Responsive Layout

| # | Test | Expected |
|---|------|----------|
| UI-01 | Open dashboard at 1920 × 1080 | All panels visible, no overflow |
| UI-02 | Open at 768 × 1024 (tablet) | Layout reflows to single column or 2 col |
| UI-03 | Open at 375 × 812 (mobile) | Cards stack, no horizontal scroll |
| UI-04 | Resize window dynamically | Charts resize without breaking |

### 5.2 Login Form

| # | Test | Expected |
|---|------|----------|
| UI-05 | Submit blank email/password | Validation message shown |
| UI-06 | Submit wrong credentials | Error toast/message shown |
| UI-07 | Submit correct credentials | Redirect to dashboard, JWT stored |
| UI-08 | Reload dashboard while logged in | Remains authenticated |
| UI-09 | Delete JWT from localStorage, reload | Redirect to login |

### 5.3 Charts

| # | Test | Expected |
|---|------|----------|
| UI-10 | Dashboard auto-refresh fires | Chart updates with new data point |
| UI-11 | Select custom date range for history | Chart shows only that period |
| UI-12 | No data for selected range | Chart shows empty state message |
| UI-13 | Hover over chart data point | Tooltip shows value and timestamp |

### 5.4 Alerts Panel

| # | Test | Expected |
|---|------|----------|
| UI-14 | Active alerts shown with severity badge | Correct colour coding (red=critical, yellow=warning) |
| UI-15 | Click "Mark as Read" | Alert moves to read state, count decrements |
| UI-16 | No active alerts | Panel shows "No active alerts" message |

---

## 6. Performance Acceptance Criteria

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| API response time (GET /api/sensors/latest) | < 200 ms (p95) | `curl -w "%{time_total}"` |
| API response time (GET /api/sensors/history, limit=100) | < 500 ms (p95) | `curl -w "%{time_total}"` |
| ESP32 to DB write latency | < SEND_INTERVAL + 1 s | Compare ESP32 serial timestamp to DB `created_at` |
| Dashboard render time (first load) | < 3 s on 10 Mbps | Chrome DevTools → Network tab |
| Concurrent API users | 20 simultaneous requests without errors | `ab -n 200 -c 20 http://localhost:8000/api/sensors/latest` |
| DB table size (1 year, 1 device, 5 s interval) | ≈ 6.3 M rows; query < 1 s with index | `EXPLAIN SELECT ...` with date range |
| Uptime target | 99 % over 30 days | Monitoring ping every 60 s |

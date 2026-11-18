# Setup and deployment

## 1. Database

Install MySQL 8 and create the database and application user. You can use the included schema after creating the database:

```sql
CREATE DATABASE weather_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'weather_app'@'%' IDENTIFIED BY 'use-a-strong-password';
GRANT ALL PRIVILEGES ON weather_db.* TO 'weather_app'@'%';
```

Run `database/schema.sql` against `weather_db` if you want to create tables manually. The API also creates missing tables at startup. Do not use the placeholder admin password hash from the SQL file; register an account through the site and promote it after:

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

## 2. Start the API

From the `backend` directory, create a virtual environment, install the requirements, and copy `.env.example` to `.env`. Set `DATABASE_URL` to your MySQL credentials and replace `SECRET_KEY` with a unique random value. Set `CORS_ORIGINS` to the exact origin serving the frontend (comma-separated when there is more than one).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is at `http://localhost:8000`; interactive API docs are at `/docs`.

## 3. Start the frontend

From the project root, serve `frontend` over HTTP:

```bash
python -m http.server 3000 --directory frontend
```

Open `http://localhost:3000`. The client uses `http://localhost:8000` by default; change `window.WEATHER_API_BASE` in `frontend/assets/js/config.js` for another API host. Create a user through **Register**, then promote the account to admin using the SQL above if settings administration is needed.

## 4. Connect an ESP32

Install the Arduino ESP32 board package plus the DHT, Adafruit BMP280, and ArduinoJson libraries. Set Wi-Fi credentials, `serverURL`, and `deviceCode` in `esp32/weather_monitor.ino`, then flash the board. The board must be able to reach the API over HTTP. For a local network, use the computer's LAN address instead of `localhost`; for a public deployment, use HTTPS and a reachable API hostname.

The sketch sends temperature (°C), humidity (%), pressure (hPa), rain state, and raw MQ-135 ADC (0–4095) every five seconds. Check the Arduino serial monitor and `/docs` when diagnosing connectivity.

## Deployment notes

Deploy the API as a Python web service with start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; provide `DATABASE_URL`, `SECRET_KEY`, and `CORS_ORIGINS` as deployment environment variables. Use a managed MySQL service or a VPS-hosted MySQL instance with network access restricted to the API. Serve the static `frontend` directory with any static host and set CORS to that exact origin. Do not commit `.env` or expose database credentials in the frontend. ESP32 firmware configured for HTTPS requires a TLS-capable deployment and a suitable certificate strategy; avoid sending credentials over public plain HTTP.

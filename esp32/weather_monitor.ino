/*
 * ============================================================
 * Smart Weather Monitoring System — ESP32 Firmware
 * ============================================================
 * Board  : ESP32 (any variant with ADC & I2C)
 * IDE    : Arduino IDE 2.x + ESP32 board support
 *
 * Required libraries (install via Arduino Library Manager):
 *   - WiFi.h          — built-in with ESP32 board package
 *   - HTTPClient.h    — built-in with ESP32 board package
 *   - DHT sensor library  (Adafruit)   Search: "DHT sensor library"
 *   - Adafruit_BMP280     (Adafruit)   Search: "Adafruit BMP280"
 *   - ArduinoJson         (Benoit Blanc) Search: "ArduinoJson"
 *
 * ⚠️  MQ-135 WARM-UP NOTICE
 *     The MQ-135 air-quality sensor requires a 24–48 hour
 *     pre-heat period before its readings are accurate.
 *     During initial power-up the raw ADC values will be
 *     elevated; treat them as approximate until the sensor
 *     has stabilised.
 * ============================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION — edit these before uploading =====
const char* ssid        = "YOUR_WIFI_SSID";
const char* password    = "YOUR_WIFI_PASSWORD";
const char* serverURL   = "http://YOUR_SERVER_IP:8000/api/sensors/readings";
const char* deviceCode  = "ESP32_WEATHER_01";
const int   SEND_INTERVAL = 5000;   // milliseconds between data sends
// =======================================================

// ── Pin definitions ─────────────────────────────────────
#define DHTPIN           4   // DHT22 data line
#define DHTTYPE          DHT22
#define RAIN_SENSOR_PIN  34  // Rain sensor — analog output (A0)
#define MQ135_PIN        35  // MQ-135    — analog output (A0)
#define RAIN_DIGITAL_PIN 27  // Rain sensor — digital output (D0); LOW = rain detected

// ── Sensor objects ──────────────────────────────────────
DHT          dht(DHTPIN, DHTTYPE);
Adafruit_BMP280 bmp;   // default I2C: SDA→GPIO21, SCL→GPIO22

// ── Sensor validation limits ────────────────────────────
const float TEMP_MIN  = -40.0,  TEMP_MAX  = 85.0;
const float HUM_MIN   =   0.0,  HUM_MAX   = 100.0;
const float PRES_MIN  = 300.0,  PRES_MAX  = 1100.0;
const int   AQ_MIN    =    0,   AQ_MAX    = 4095;

// ────────────────────────────────────────────────────────
// connectWiFi() — attempt to join AP; retry up to 10 times
// ────────────────────────────────────────────────────────
void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 10) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("[WiFi] Connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("[WiFi] ⚠ Failed to connect. Will retry in next loop.");
  }
}

// ────────────────────────────────────────────────────────
// setup() — runs once on boot
// ────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== Smart Weather Monitor Booting ===");

  // ── Initialise DHT22 ──────────────────────────────────
  // DHT22: measures temperature (−40 to +80 °C) and
  // relative humidity (0–100 %). Requires pull-up on DATA.
  dht.begin();
  Serial.println("[DHT22] Initialised on GPIO " + String(DHTPIN));

  // ── Initialise BMP280 ─────────────────────────────────
  // BMP280: measures barometric pressure & temperature via I2C.
  // Default I2C address: 0x76 (SDO→GND) or 0x77 (SDO→VCC).
  if (!bmp.begin(0x76)) {
    Serial.println("[BMP280] ⚠ Sensor not found at 0x76, trying 0x77...");
    if (!bmp.begin(0x77)) {
      Serial.println("[BMP280] ✗ Not found! Check wiring.");
    } else {
      Serial.println("[BMP280] Initialised at 0x77");
    }
  } else {
    Serial.println("[BMP280] Initialised at 0x76");
  }

  // Recommended oversampling settings for weather monitoring
  bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                  Adafruit_BMP280::SAMPLING_X2,   // temperature
                  Adafruit_BMP280::SAMPLING_X16,  // pressure
                  Adafruit_BMP280::FILTER_X16,
                  Adafruit_BMP280::STANDBY_MS_500);

  // ── Configure ADC pins ────────────────────────────────
  // GPIO34 & GPIO35 are input-only on ESP32; no pinMode needed.
  pinMode(RAIN_DIGITAL_PIN, INPUT);
  Serial.println("[GPIO] Rain digital pin configured: GPIO " + String(RAIN_DIGITAL_PIN));

  // ── Connect to WiFi ───────────────────────────────────
  connectWiFi();

  Serial.println("=== Setup complete — entering loop ===");
}

// ────────────────────────────────────────────────────────
// loop() — runs repeatedly
// ────────────────────────────────────────────────────────
void loop() {

  // ── Step 1: Ensure WiFi is connected ──────────────────
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Disconnected — attempting reconnect...");
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[WiFi] Still disconnected; skipping this cycle.");
      delay(SEND_INTERVAL);
      return;
    }
  }

  // ── Step 2: Read DHT22 — temperature & humidity ───────
  // Allow at least 2 s between DHT reads (sensor limitation).
  float temperature = dht.readTemperature();  // Celsius
  float humidity    = dht.readHumidity();     // %RH

  // ── Step 3: Validate DHT readings; retry once if NaN ──
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[DHT22] Bad reading — retrying after 100 ms...");
    delay(100);
    temperature = dht.readTemperature();
    humidity    = dht.readHumidity();
  }
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[DHT22] ✗ Failed to read sensor. Skipping cycle.");
    delay(SEND_INTERVAL);
    return;
  }
  Serial.printf("[DHT22] Temperature: %.1f °C | Humidity: %.1f %%\n",
                temperature, humidity);

  // ── Step 4: Read BMP280 — barometric pressure ─────────
  // readPressure() returns Pa; divide by 100 to get hPa.
  float pressure = bmp.readPressure() / 100.0F;
  Serial.printf("[BMP280] Pressure: %.1f hPa\n", pressure);

  // ── Step 5: Read rain sensor ──────────────────────────
  // Analog value: low voltage ≈ rain present (resistance drops).
  // Digital pin: LOW when rain is detected (comparator output).
  int  rainAnalog   = analogRead(RAIN_SENSOR_PIN);
  bool rainDetected = (digitalRead(RAIN_DIGITAL_PIN) == LOW);
  Serial.printf("[Rain] Analog: %d | Detected: %s\n",
                rainAnalog, rainDetected ? "YES" : "NO");

  // ── Step 6: Read MQ-135 — air quality ─────────────────
  // Returns raw 12-bit ADC value (0–4095).
  // Higher value = higher gas concentration.
  // ⚠ See warm-up notice at top of file.
  int airQualityRaw = analogRead(MQ135_PIN);
  Serial.printf("[MQ-135] Raw ADC: %d\n", airQualityRaw);

  // ── Step 7: Validate all readings are within range ────
  if (temperature < TEMP_MIN || temperature > TEMP_MAX) {
    Serial.printf("[Validation] Temperature %.1f out of range!\n", temperature);
    delay(SEND_INTERVAL); return;
  }
  if (humidity < HUM_MIN || humidity > HUM_MAX) {
    Serial.printf("[Validation] Humidity %.1f out of range!\n", humidity);
    delay(SEND_INTERVAL); return;
  }
  if (pressure < PRES_MIN || pressure > PRES_MAX) {
    Serial.printf("[Validation] Pressure %.1f out of range!\n", pressure);
    delay(SEND_INTERVAL); return;
  }
  if (airQualityRaw < AQ_MIN || airQualityRaw > AQ_MAX) {
    Serial.printf("[Validation] Air quality %d out of range!\n", airQualityRaw);
    delay(SEND_INTERVAL); return;
  }

  // ── Step 8: Build JSON payload ────────────────────────
  StaticJsonDocument<256> doc;
  doc["device_code"]    = deviceCode;
  doc["temperature"]    = round(temperature * 10.0) / 10.0;
  doc["humidity"]       = round(humidity    * 10.0) / 10.0;
  doc["pressure"]       = round(pressure    * 10.0) / 10.0;
  doc["rain_detected"]  = rainDetected;
  doc["air_quality_raw"] = airQualityRaw;

  String jsonPayload;
  serializeJson(doc, jsonPayload);
  Serial.println("[JSON] Payload: " + jsonPayload);

  // ── Step 9: HTTP POST to backend ──────────────────────
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  Serial.println("[HTTP] Sending POST to: " + String(serverURL));
  int httpResponseCode = http.POST(jsonPayload);

  // ── Step 10: Print response ───────────────────────────
  if (httpResponseCode > 0) {
    String responseBody = http.getString();
    Serial.printf("[HTTP] Response code: %d\n", httpResponseCode);
    Serial.println("[HTTP] Response body: " + responseBody);
  } else {
    Serial.printf("[HTTP] ✗ Error: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();

  // ── Step 11: Wait before next reading ─────────────────
  Serial.printf("[Loop] Waiting %d ms...\n\n", SEND_INTERVAL);
  delay(SEND_INTERVAL);
}

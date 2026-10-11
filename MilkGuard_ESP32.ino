/*
 * MilkGuard ESP32 -> existing live Flask backend
 * Sends readings to POST https://milk-guard.onrender.com/predict
 * JSON format expected by app.py: {"sample_id":"...","ph":...,"tds":...,"temperature":...}
 *
 * Arduino IDE libraries: OneWire, DallasTemperature
 * IMPORTANT: calibrate pH/TDS sensors before relying on readings.
 * The pH/TDS conversion functions below are placeholders, not universal formulas.
 */
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Replace these locally; do not upload real Wi-Fi credentials to a public repo.
const char* WIFI_SSID = "srivastava___aryan";
const char* WIFI_PASSWORD = "Anujashish";
const char* API_URL = "https://milk-guard.onrender.com/predict";

constexpr int PH_PIN = 34;       // ADC input only
constexpr int TDS_PIN = 35;      // ADC input only
constexpr int DS18B20_PIN = 4;
constexpr unsigned long SEND_INTERVAL_MS = 30000;

OneWire oneWire(DS18B20_PIN);
DallasTemperature tempSensor(&oneWire);
unsigned long lastSend = 0;
uint32_t sampleCounter = 0;

float readPH() {
  // Placeholder mapping. Calibrate with pH 4.00 / 7.00 buffer solutions.
  const int raw = analogRead(PH_PIN);
  const float voltage = raw * 3.3f / 4095.0f;
  return 7.0f + ((2.5f - voltage) / 0.18f);
}

float readTDS() {
  // Placeholder conversion. Calibrate for your exact TDS module and solution.
  const int raw = analogRead(TDS_PIN);
  const float voltage = raw * 3.3f / 4095.0f;
  const float compensation = 1.0f; // Add temperature compensation after calibration.
  return compensation * (133.42f * voltage * voltage * voltage
      - 255.86f * voltage * voltage + 857.39f * voltage) * 0.5f;
}

bool readingsLookValid(float ph, float tds, float tempC) {
  return isfinite(ph) && isfinite(tds) && isfinite(tempC)
      && ph >= 0.0f && ph <= 14.0f
      && tds >= 0.0f && tds <= 5000.0f
      && tempC >= -10.0f && tempC <= 100.0f
      && tempC != DEVICE_DISCONNECTED_C;
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connecting to Wi-Fi: %s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected. ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi connection timed out; will retry later.");
  }
}

void sendReading(float ph, float tds, float tempC) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Not sent: Wi-Fi is disconnected.");
    return;
  }

  // HTTPS transport. setInsecure() avoids certificate-store setup for a prototype,
  // but does not verify the server certificate. For production, install/verify the
  // appropriate root CA instead of using setInsecure().
  WiFiClientSecure tlsClient;
  tlsClient.setInsecure();
  HTTPClient http;
  http.setConnectTimeout(15000);
  http.setTimeout(15000);

  if (!http.begin(tlsClient, API_URL)) {
    Serial.println("Could not initialize HTTPS request.");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  const String sampleId = "MG-ESP32-" + String((uint32_t)ESP.getEfuseMac(), HEX)
                          + "-" + String(++sampleCounter);
  String body = "{\"sample_id\":\"" + sampleId + "\",\"ph\":" + String(ph, 2)
              + ",\"tds\":" + String(tds, 1)
              + ",\"temperature\":" + String(tempC, 2) + "}";

  Serial.println("Sending to MilkGuard API...");
  Serial.println(body);
  const int httpCode = http.POST(body);
  Serial.printf("HTTP status: %d\n", httpCode);
  if (httpCode > 0) {
    Serial.println("API response:");
    Serial.println(http.getString());
  } else {
    Serial.printf("HTTPS request failed: %s\n", HTTPClient::errorToString(httpCode).c_str());
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(300);
  analogReadResolution(12);
  analogSetPinAttenuation(PH_PIN, ADC_11db);
  analogSetPinAttenuation(TDS_PIN, ADC_11db);
  tempSensor.begin();
  connectWiFi();
  Serial.println("MilkGuard ESP32 sensor sender ready.");
  Serial.println("Open Serial Monitor at 115200 baud.");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  if (lastSend == 0 || millis() - lastSend >= SEND_INTERVAL_MS) {
    lastSend = millis();
    tempSensor.requestTemperatures();
    const float ph = readPH();
    const float tds = readTDS();
    const float tempC = tempSensor.getTempCByIndex(0);

    Serial.printf("Readings: pH=%.2f, TDS=%.1f ppm, Temp=%.2f C\n", ph, tds, tempC);
    if (readingsLookValid(ph, tds, tempC)) {
      sendReading(ph, tds, tempC);
    } else {
      Serial.println("Not sent: invalid reading. Check DS18B20 wiring and sensor calibration.");
    }
  }
  delay(100);
}

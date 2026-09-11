// Read sensors on ESP32, then send values to the Flask API over Wi-Fi.
// Library Manager se install karo: OneWire aur DallasTemperature.
// pH/TDS formula starting point hai; real project mein calibration compulsory hai.
#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://192.168.1.10:5000/predict"; // laptop's local IP
const int phPin = 34;
const int tdsPin = 35;
const int tempPin = 4;
OneWire oneWire(tempPin);
DallasTemperature temperatureSensor(&oneWire);

float readPH() {
  int raw = analogRead(phPin);
  float voltage = raw * 3.3 / 4095.0;
  // Adjust 7.0 and 2.5 after calibrating with pH buffer solutions.
  return 7.0 + ((2.5 - voltage) / 0.18);
}

float readTDS() {
  int raw = analogRead(tdsPin);
  float voltage = raw * 3.3 / 4095.0;
  // Starting conversion only; use the calibration procedure for your TDS module.
  return (133.42 * voltage * voltage * voltage - 255.86 * voltage * voltage + 857.39 * voltage) * 0.5;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  temperatureSensor.begin();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
}

void loop() {
  temperatureSensor.requestTemperatures();
  float ph = readPH();
  float tds = readTDS();
  float temperature = temperatureSensor.getTempCByIndex(0);
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    String body = "{\"ph\":" + String(ph, 2) + ",\"tds\":" + String(tds, 0) + ",\"temperature\":" + String(temperature, 1) + "}";
    int code = http.POST(body);
    Serial.println(http.getString());
    http.end();
  }
  delay(30000);
}

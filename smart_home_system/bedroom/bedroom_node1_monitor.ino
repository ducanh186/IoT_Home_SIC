/*
 * BEDROOM NODE 1 - Environmental Monitor & Safety System
 * ESP32 NodeMCU + Sensors
 * 
 * CHỨC NĂNG:
 * ✅ Giám sát nhiệt độ và độ ẩm (DHT11)
 * ✅ Phát hiện khí gas 3 cấp độ (MQ Sensor)
 * ✅ Phát hiện cháy (Flame Sensor)  
 * ✅ Điều khiển LED và Buzzer cảnh báo
 * ✅ Gửi dữ liệu qua MQTT theo cấu trúc mới
 * ✅ Tự động kết nối lại WiFi/MQTT
 * 
 * HARDWARE CONFIGURATION:
 * - DHT11: GPIO 4 (Temperature & Humidity)
 * - MQ Gas Sensor: GPIO 34 (Analog), GPIO 35 (Digital)
 * - Flame Sensor: GPIO 26 (Digital)
 * - Green LED: GPIO 18 (SAFE)
 * - Yellow LED: GPIO 19 (WARNING)
 * - Red LED: GPIO 21 (DANGER)
 * - Buzzer: GPIO 5 (PWM)
 * 
 * MQTT TOPICS:
 * - home/bedroom/node1/temperature_sensor/value
 * - home/bedroom/node1/humidity_sensor/value
 * - home/bedroom/node1/gas_sensor/analog_value
 * - home/bedroom/node1/gas_sensor/status
 * - home/bedroom/node1/flame_sensor/alert
 * - home/bedroom/node1/led_system/status
 * - home/bedroom/node1/buzzer/status
 */

#include "DHT.h"
#include "PubSubClient.h"
#include "WiFi.h"
#include <ArduinoJson.h>

// ===== NETWORK CONFIGURATION =====
const char* WIFI_SSID = "SSIoT-02";
const char* WIFI_PASSWORD = "SSIoT-02";

// ===== MQTT BROKER CONFIGURATION =====
const char* MQTT_SERVER = "pi101.local";  // hoặc "raspberrypi"
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "pi101";
const char* MQTT_PASSWORD = "1234";
const char* MQTT_SERVER_IP = "192.168.1.3"; // Backup IP

// ===== MQTT TOPICS =====
#define BEDROOM_NODE1_TEMP_TOPIC        "home/bedroom/node1/temperature_sensor/value"
#define BEDROOM_NODE1_HUMIDITY_TOPIC    "home/bedroom/node1/humidity_sensor/value"
#define BEDROOM_NODE1_GAS_ANALOG_TOPIC  "home/bedroom/node1/gas_sensor/analog_value"
#define BEDROOM_NODE1_GAS_STATUS_TOPIC  "home/bedroom/node1/gas_sensor/status"
#define BEDROOM_NODE1_FLAME_TOPIC       "home/bedroom/node1/flame_sensor/alert"
#define BEDROOM_NODE1_LED_STATUS_TOPIC  "home/bedroom/node1/led_system/status"
#define BEDROOM_NODE1_BUZZER_TOPIC      "home/bedroom/node1/buzzer/status"

// ===== SYSTEM STATUS TOPICS =====
#define SYSTEM_STATUS_TOPIC     "home/system/status"
#define SYSTEM_HEARTBEAT_TOPIC  "home/system/heartbeat"

// ===== CLIENT ID =====
#define BEDROOM_NODE1_CLIENT_ID "ESP32_Bedroom_Node1_Monitor"

// ===== TIMING CONSTANTS =====
#define MQTT_RECONNECT_DELAY    5000   // 5 seconds
#define HEARTBEAT_INTERVAL      30000  // 30 seconds
#define SENSOR_READ_INTERVAL    2000   // 2 seconds

// ===== HARDWARE CONFIGURATION =====
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// MQ Gas Sensor
#define MQ_ANALOG_PIN 34
#define MQ_DIGITAL_PIN 35
#define GAS_SAFE_THRESHOLD 1400
#define GAS_WARNING_THRESHOLD 1600

// Fire Sensor
#define FIRE_SENSOR_PIN 26

// LED Indicators
#define GREEN_LED_PIN 18
#define YELLOW_LED_PIN 19
#define RED_LED_PIN 21

// Buzzer PWM
#define BUZZER_PIN 5
#define BUZZER_CHANNEL 0
#define BUZZER_FREQUENCY 2000
#define BUZZER_RESOLUTION 8

// Gas Level Enumeration
enum GasLevel {
  GAS_SAFE,
  GAS_WARNING,
  GAS_DANGER
};

// System Data Structure
struct SensorData {
  float temperature;
  float humidity;
  int gasAnalogValue;
  bool gasDigitalTriggered;
  GasLevel gasLevel;
  bool fireDetected;
  bool isDataValid;
  unsigned long timestamp;
};

// WiFi and MQTT objects
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Global variables
unsigned long lastSensorRead = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastMQTTAttempt = 0;

// ===== SETUP FUNCTION =====
void setup() {
  Serial.begin(115200);
  Serial.println("\n🏠 BEDROOM NODE 1 - Environmental Monitor Starting...");
  
  initializeHardware();
  connectToWiFi();
  setupMQTT();
  
  Serial.println("✅ Bedroom Node 1 initialized successfully!");
  Serial.println("📊 Starting environmental monitoring...\n");
}

// ===== MAIN LOOP =====
void loop() {
  maintainConnections();
  
  if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
    SensorData data = readAllSensors();
    
    if (data.isDataValid) {
      controlLEDsAndBuzzer(data);
      publishSensorData(data);
      displayReadings(data);
    }
    
    lastSensorRead = millis();
  }
  
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    publishHeartbeat();
    lastHeartbeat = millis();
  }
  
  client.loop();
  delay(100);
}

// ===== HARDWARE INITIALIZATION =====
void initializeHardware() {
  Serial.println("🔧 Initializing hardware...");
  
  // DHT11
  dht.begin();
  Serial.println("  ✅ DHT11 (GPIO 4)");
  
  // MQ Gas Sensor
  pinMode(MQ_ANALOG_PIN, INPUT);
  pinMode(MQ_DIGITAL_PIN, INPUT);
  Serial.println("  ✅ MQ Gas Sensor (GPIO 34, 35)");
  
  // Flame Sensor
  pinMode(FIRE_SENSOR_PIN, INPUT);
  Serial.println("  ✅ Flame Sensor (GPIO 26)");
  
  // LEDs
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.println("  ✅ LED System (GPIO 18,19,21)");
  
  // Buzzer PWM
  pinMode(BUZZER_PIN, OUTPUT);
  #if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcAttach(BUZZER_PIN, BUZZER_FREQUENCY, BUZZER_RESOLUTION);
    ledcWrite(BUZZER_PIN, 0);
  #else
    ledcSetup(BUZZER_CHANNEL, BUZZER_FREQUENCY, BUZZER_RESOLUTION);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHANNEL);
    ledcWrite(BUZZER_CHANNEL, 0);
  #endif
  Serial.println("  ✅ Buzzer PWM (GPIO 5)");
  
  testLEDs();
}

void testLEDs() {
  Serial.println("  🔍 Testing LEDs...");
  digitalWrite(GREEN_LED_PIN, HIGH);
  delay(200);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, HIGH);
  delay(200);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
  delay(200);
  digitalWrite(RED_LED_PIN, LOW);
}

// ===== WIFI CONNECTION =====
void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  // Cấu hình WiFi cho mobile hotspot
  WiFi.mode(WIFI_STA);
  WiFi.setAutoConnect(true);
  WiFi.setAutoReconnect(true);
  
  // Tăng cường độ tín hiệu (cho mobile hotspot)
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  
  // Bắt đầu kết nối
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) { // Tăng attempts cho mobile hotspot
    delay(500);
    Serial.print(".");
    attempts++;
    
    // Retry mỗi 10 attempts
    if (attempts % 10 == 0) {
      Serial.println("");
      Serial.printf("⚠️ Attempt %d/40 - Retrying WiFi connection...\n", attempts);
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    Serial.print("🌐 Gateway: ");
    Serial.println(WiFi.gatewayIP());
  } else {
    Serial.println("\n❌ WiFi connection failed after 40 attempts!");
    Serial.println("💡 Check: WiFi name, password, and mobile hotspot range");
  }
}

// ===== MQTT SETUP =====
void setupMQTT() {
  // Cấu hình timeout cho mobile hotspot (thường chậm hơn)
  client.setKeepAlive(60);  // Tăng keepalive cho mobile hotspot
  client.setSocketTimeout(30); // Tăng timeout
  
  // Thử kết nối với hostname trước
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(mqttCallback);
  
  Serial.printf("🔗 Trying MQTT connection to %s:%d\n", MQTT_SERVER, MQTT_PORT);
  
  if (!connectToMQTT()) {
    // Nếu hostname không hoạt động, thử IP backup
    Serial.println("⚠️ Hostname failed, trying backup IP...");
    client.setServer(MQTT_SERVER_IP, MQTT_PORT);
    Serial.printf("🔗 Trying MQTT connection to %s:%d\n", MQTT_SERVER_IP, MQTT_PORT);
    connectToMQTT();
  }
}

bool connectToMQTT() {
  if (WiFi.status() != WL_CONNECTED) return false;
  
  Serial.print("📡 Connecting to MQTT broker...");
  
  // Thử kết nối 3 lần với mobile hotspot
  for (int attempt = 1; attempt <= 3; attempt++) {
    Serial.printf(" (Attempt %d/3)", attempt);
    
    if (client.connect(BEDROOM_NODE1_CLIENT_ID)) {  // Không dùng username/password vì đã tắt auth
      Serial.println(" ✅ Connected!");
      publishOnlineStatus();
      return true;
    } else {
      Serial.printf(" ❌ Failed, rc=%d", client.state());
      if (attempt < 3) {
        Serial.print(" - Retrying in 2s...");
        delay(2000);
      }
    }
  }
  
  Serial.println("");
  Serial.println("🚨 MQTT connection completely failed after 3 attempts");
  return false;
}

void maintainConnections() {
  // Check WiFi với logic mạnh mẽ hơn cho mobile hotspot
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi disconnected, reconnecting...");
    Serial.printf("🔍 WiFi status: %d\n", WiFi.status());
    
    // Thử kết nối lại với retry logic
    for (int retry = 0; retry < 3; retry++) {
      Serial.printf("🔄 Reconnection attempt %d/3...\n", retry + 1);
      
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      
      // Đợi kết nối với timeout
      int waitTime = 0;
      while (WiFi.status() != WL_CONNECTED && waitTime < 15) {
        delay(1000);
        Serial.print(".");
        waitTime++;
      }
      
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ WiFi reconnected successfully!");
        Serial.printf("📶 Signal: %d dBm\n", WiFi.RSSI());
        break;
      } else {
        Serial.println("\n❌ Reconnection failed, trying again...");
      }
    }
    
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("🚨 WiFi connection completely failed - restarting ESP32 in 30s");
      delay(30000);
      ESP.restart();
    }
    return;
  }
  
  // Check MQTT
  if (!client.connected() && millis() - lastMQTTAttempt >= MQTT_RECONNECT_DELAY) {
    Serial.println("⚠️ MQTT disconnected, reconnecting...");
    connectToMQTT();
    lastMQTTAttempt = millis();
  }
}

// ===== SENSOR READING =====
SensorData readAllSensors() {
  SensorData data;
  data.timestamp = millis() / 1000;
  
  // Read DHT11
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  if (isnan(data.temperature) || isnan(data.humidity)) {
    data.isDataValid = false;
    Serial.println("❌ DHT11 reading failed!");
    return data;
  }
  
  // Read Gas Sensor
  data.gasAnalogValue = analogRead(MQ_ANALOG_PIN);
  data.gasDigitalTriggered = (digitalRead(MQ_DIGITAL_PIN) == LOW);
  
  // Determine gas level
  if (data.gasAnalogValue < GAS_SAFE_THRESHOLD) {
    data.gasLevel = GAS_SAFE;
  } else if (data.gasAnalogValue < GAS_WARNING_THRESHOLD) {
    data.gasLevel = GAS_WARNING;
  } else {
    data.gasLevel = GAS_DANGER;
  }
  
  // Read Fire Sensor
  data.fireDetected = (digitalRead(FIRE_SENSOR_PIN) == HIGH);
  
  data.isDataValid = true;
  return data;
}

// ===== LED & BUZZER CONTROL =====
void controlLEDsAndBuzzer(const SensorData& data) {
  static unsigned long lastFlash = 0;
  static bool flashState = false;
  
  // Fire Emergency: All LEDs flash
  if (data.fireDetected) {
    if (millis() - lastFlash >= 200) {
      flashState = !flashState;
      digitalWrite(GREEN_LED_PIN, flashState);
      digitalWrite(YELLOW_LED_PIN, flashState);
      digitalWrite(RED_LED_PIN, flashState);
      
      // Fire buzzer (continuous high frequency)
      playBuzzer(200, flashState);
      lastFlash = millis();
    }
  }
  // Normal gas level indication
  else {
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(YELLOW_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, LOW);
    
    switch (data.gasLevel) {
      case GAS_SAFE:
        digitalWrite(GREEN_LED_PIN, HIGH);
        playBuzzer(0, false); // Silent
        break;
      case GAS_WARNING:
        digitalWrite(YELLOW_LED_PIN, HIGH);
        // Warning buzzer (slow beep)
        if (millis() - lastFlash >= 1000) {
          flashState = !flashState;
          playBuzzer(120, flashState);
          lastFlash = millis();
        }
        break;
      case GAS_DANGER:
        digitalWrite(RED_LED_PIN, HIGH);
        // Danger buzzer (fast beep)
        if (millis() - lastFlash >= 500) {
          flashState = !flashState;
          playBuzzer(180, flashState);
          lastFlash = millis();
        }
        break;
    }
  }
}

void playBuzzer(int intensity, bool enable) {
  if (enable && intensity > 0) {
    #if ESP_ARDUINO_VERSION_MAJOR >= 3
      ledcWrite(BUZZER_PIN, intensity);
    #else
      ledcWrite(BUZZER_CHANNEL, intensity);
    #endif
  } else {
    #if ESP_ARDUINO_VERSION_MAJOR >= 3
      ledcWrite(BUZZER_PIN, 0);
    #else
      ledcWrite(BUZZER_CHANNEL, 0);
    #endif
  }
}

// ===== MQTT PUBLISHING =====
void publishSensorData(const SensorData& data) {
  if (!client.connected()) return;
  
  // Temperature
  String tempStr = String(data.temperature, 1);
  client.publish(BEDROOM_NODE1_TEMP_TOPIC, tempStr.c_str());
  
  // Humidity
  String humStr = String(data.humidity, 1);
  client.publish(BEDROOM_NODE1_HUMIDITY_TOPIC, humStr.c_str());
  
  // Gas analog value
  String gasAnalogStr = String(data.gasAnalogValue);
  client.publish(BEDROOM_NODE1_GAS_ANALOG_TOPIC, gasAnalogStr.c_str());
  
  // Gas status
  String gasStatus;
  switch (data.gasLevel) {
    case GAS_SAFE: gasStatus = "SAFE"; break;
    case GAS_WARNING: gasStatus = "WARNING"; break;
    case GAS_DANGER: gasStatus = "DANGER"; break;
  }
  client.publish(BEDROOM_NODE1_GAS_STATUS_TOPIC, gasStatus.c_str());
  
  // Fire alert
  String fireStatus = data.fireDetected ? "FIRE_DETECTED" : "NO_FIRE";
  client.publish(BEDROOM_NODE1_FLAME_TOPIC, fireStatus.c_str());
  
  // LED status
  StaticJsonDocument<200> ledDoc;
  ledDoc["green"] = digitalRead(GREEN_LED_PIN);
  ledDoc["yellow"] = digitalRead(YELLOW_LED_PIN);
  ledDoc["red"] = digitalRead(RED_LED_PIN);
  String ledStatus;
  serializeJson(ledDoc, ledStatus);
  client.publish(BEDROOM_NODE1_LED_STATUS_TOPIC, ledStatus.c_str());
  
  // Buzzer status
  StaticJsonDocument<100> buzzerDoc;
  buzzerDoc["active"] = (data.fireDetected || data.gasLevel != GAS_SAFE);
  buzzerDoc["level"] = data.fireDetected ? "FIRE" : (data.gasLevel == GAS_DANGER ? "DANGER" : (data.gasLevel == GAS_WARNING ? "WARNING" : "OFF"));
  String buzzerStatus;
  serializeJson(buzzerDoc, buzzerStatus);
  client.publish(BEDROOM_NODE1_BUZZER_TOPIC, buzzerStatus.c_str());
}

void publishHeartbeat() {
  if (!client.connected()) return;
  
  StaticJsonDocument<200> doc;
  doc["room"] = "bedroom";
  doc["node"] = "node1";
  doc["type"] = "environmental_monitor";
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["timestamp"] = millis() / 1000;
  
  String heartbeat;
  serializeJson(doc, heartbeat);
  client.publish(SYSTEM_HEARTBEAT_TOPIC, heartbeat.c_str());
}

void publishOnlineStatus() {
  if (!client.connected()) return;
  
  StaticJsonDocument<150> doc;
  doc["room"] = "bedroom";
  doc["node"] = "node1";
  doc["status"] = "online";
  doc["ip"] = WiFi.localIP().toString();
  doc["timestamp"] = millis() / 1000;
  
  String status;
  serializeJson(doc, status);
  client.publish(SYSTEM_STATUS_TOPIC, status.c_str());
}

// ===== DISPLAY FUNCTIONS =====
void displayReadings(const SensorData& data) {
  Serial.println("╔═══════════════════════════════════════════╗");
  Serial.println("║        🏠 BEDROOM NODE 1 - Monitor       ║");
  Serial.println("╠═══════════════════════════════════════════╣");
  Serial.printf("║ 🌡️  Temperature: %6.1f°C              ║\n", data.temperature);
  Serial.printf("║ 💧 Humidity:    %6.1f%%               ║\n", data.humidity);
  Serial.printf("║ 💨 Gas Level:   %4d (%s)            ║\n", 
                data.gasAnalogValue,
                data.gasLevel == GAS_SAFE ? "SAFE" : 
                data.gasLevel == GAS_WARNING ? "WARNING" : "DANGER");
  Serial.printf("║ 🔥 Fire:        %-9s              ║\n", 
                data.fireDetected ? "DETECTED" : "NO FIRE");
  
  if (data.fireDetected) {
    Serial.println("║ 🚨🔥 FIRE EMERGENCY - EVACUATE! 🔥🚨    ║");
  } else if (data.gasLevel == GAS_DANGER) {
    Serial.println("║ ⚠️🚨  GAS DANGER - VENTILATE!  🚨⚠️     ║");
  } else if (data.gasLevel == GAS_WARNING) {
    Serial.println("║ ⚠️⚠️  GAS WARNING - MONITOR  ⚠️⚠️       ║");
  } else {
    Serial.println("║ ✅✅ Environment SAFE - Normal ✅✅     ║");
  }
  
  Serial.println("╚═══════════════════════════════════════════╝\n");
}

// ===== MQTT CALLBACK =====
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("📨 MQTT [%s]: %s\n", topic, message.c_str());
  
  // Handle any commands if needed
  // Currently this node only publishes data
}

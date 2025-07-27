/* 
 * NODE 1 - Environmental & Fire Safety Monitoring System
 * ESP32 NodeMCU + Raspberry Pi 5
 * 
 * Features:
 * - Temperature & Humidity monitoring using DHT11 sensor (IMPLEMENTED)
 * - Gas detection using MQ sensor with 3-level warning system (IMPLEMENTED)
 * - Fire detection using flame sensor (IMPLEMENTED)
 * - LED indicator system: Green/Yellow/Red for gas levels (IMPLEMENTED)
 * - Buzzer alert system for fire and gas warnings (IMPLEMENTED)
 * - Real-time data transmission via MQTT to Raspberry Pi 5
 * - WiFi connectivity with auto-reconnection
 * - Robust error handling and sensor validation
 * 
 * Hardware: ESP32 NodeMCU
 * Pin Configuration:
 * - DHT11: GPIO 4
 * - MQ Gas Sensor: GPIO 34 (ADC1_CH6)
 * - Flame Sensor: GPIO 2
 * - Green LED: GPIO 18
 * - Yellow LED: GPIO 19
 * - Red LED: GPIO 21
 * - Buzzer: GPIO 5
 */

#include "DHT.h"
#include "PubSubClient.h"
#include "WiFi.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Initialize LCD with I2C address 0x27 and 16x2 size
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===== SECTION 1: CONFIGURATION AND DECLARATIONS =====
// DHT Sensor Configuration
#define DHTPIN 4 
#define DHTTYPE DHT11 
DHT dht(DHTPIN, DHTTYPE);

// MQ Gas Sensor Configuration (2 pins: Analog + Digital)
#define MQ_ANALOG_PIN 34         // GPIO 34 (ADC1_CH6) - Analog reading
#define MQ_DIGITAL_PIN 35        // GPIO 35 - Digital threshold detection
#define GAS_THRESHOLD_LOW 1000   // Analog: Safe level (0-4095 range)
#define GAS_THRESHOLD_MED 2000   // Analog: Warning level  
#define GAS_THRESHOLD_HIGH 3000  // Analog: Danger level

// Fire Sensor Configuration
#define FIRE_SENSOR_PIN 2        // GPIO 2 - Digital flame detection

// LED Configuration - ESP32 NodeMCU pins
#define GREEN_LED_PIN 18         // GPIO 18 - Safe status
#define YELLOW_LED_PIN 19        // GPIO 19 - Warning status
#define RED_LED_PIN 21           // GPIO 21 - Danger status

// Active Buzzer Configuration (3-pin: VCC, GND, Signal)
#define BUZZER_SIGNAL_PIN 5      // GPIO 5 - Signal control pin

// WiFi Configuration
const char* ssid = "VIETTEL";                
const char* wifi_password = "12345678";

// MQTT Configuration
const char* mqtt_server = "192.168.1.3"; // IP address of Raspberry Pi 5
const char* humidity_topic = "humidity"; // MQTT topic for humidity data
const char* temperature_topic = "temperature"; // MQTT topic for temperature data
const char* gas_analog_topic = "gas_analog"; // MQTT topic for MQ analog reading
const char* gas_digital_topic = "gas_digital"; // MQTT topic for MQ digital state
const char* gas_status_topic = "gas_status"; // MQTT topic for gas status (SAFE/WARNING/DANGER)
const char* fire_topic = "fire_detected"; // MQTT topic for fire detection
const char* mqtt_username = "pi101"; // MQTT username
const char* mqtt_password = "1234"; // MQTT password
const char* clientID = "ESP32_Safety_Monitor"; // MQTT client ID

// Initialize WiFi and MQTT objects
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient);

// Sensor data structure
struct SensorData {
  float temperature;
  float humidity;
  int gasAnalog;           // MQ analog reading (0-4095)
  bool gasDigital;         // MQ digital threshold detection
  String gasStatus;        // SAFE, WARNING, DANGER
  bool fireDetected;       // Flame sensor status
  bool isValid;
};

// Gas level enumeration
enum GasLevel {
  GAS_SAFE,
  GAS_WARNING, 
  GAS_DANGER
};

// ===== SECTION 2: SENSOR CONTROL LOGIC =====

// Initialize all sensors and hardware for ESP32
void initSensor() {
  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT11 sensor initialized on GPIO 4");
  
  // Initialize MQ gas sensor pins (ESP32 ADC + Digital)
  pinMode(MQ_ANALOG_PIN, INPUT);
  pinMode(MQ_DIGITAL_PIN, INPUT);
  Serial.println("MQ Gas sensor initialized:");
  Serial.println("  - Analog: GPIO 34 (ADC)");
  Serial.println("  - Digital: GPIO 35");
  
  // Initialize fire sensor pin
  pinMode(FIRE_SENSOR_PIN, INPUT);
  Serial.println("Flame sensor initialized on GPIO 2");
  
  // Initialize LED pins
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  Serial.println("LED indicators initialized (GPIO 18,19,21)");
  
  // Initialize active buzzer signal pin
  pinMode(BUZZER_SIGNAL_PIN, OUTPUT);
  digitalWrite(BUZZER_SIGNAL_PIN, LOW); // Ensure buzzer is off initially
  Serial.println("Active buzzer initialized on GPIO 5");
  
  // Test LEDs at startup
  testLEDs();
  Serial.println("ESP32 NodeMCU initialization complete!");
}

// Test LED functionality at startup
void testLEDs() {
  Serial.println("Testing ESP32 LEDs...");
  digitalWrite(GREEN_LED_PIN, HIGH);
  delay(300);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, HIGH);
  delay(300);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
  delay(300);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.println("LED test completed");
}

// Read MQ gas sensor (both analog and digital) - tham khảo logic từ code mẫu
GasLevel readGasLevel(int* gasAnalog, bool* gasDigital) {
  // Đọc giá trị analog (0-4095)
  *gasAnalog = analogRead(MQ_ANALOG_PIN);
  
  // Đọc giá trị digital (tương tự MQ21_getValue trong code mẫu)
  uint8_t digitalValue = digitalRead(MQ_DIGITAL_PIN);
  *gasDigital = (digitalValue == LOW) ? true : false; // LOW = gas detected
  
  // Xác định mức độ gas dựa trên giá trị analog
  if (*gasAnalog < GAS_THRESHOLD_LOW) {
    return GAS_SAFE;
  } else if (*gasAnalog < GAS_THRESHOLD_MED) {
    return GAS_WARNING;
  } else {
    return GAS_DANGER;
  }
}

// Read fire sensor - tham khảo logic flame_getValue từ code mẫu
bool readFireSensor() {
  int flame_state = digitalRead(FIRE_SENSOR_PIN);
  
  // Logic tương tự flame1_getValue trong code mẫu
  if (flame_state == HIGH) {
    return false; // Không có lửa
  } else {
    return true;  // Phát hiện lửa
  }
}

// Control LEDs based on gas level
void controlLEDs(GasLevel level) {
  // Turn off all LEDs first
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  
  // Turn on appropriate LED
  switch (level) {
    case GAS_SAFE:
      digitalWrite(GREEN_LED_PIN, HIGH);
      break;
    case GAS_WARNING:
      digitalWrite(YELLOW_LED_PIN, HIGH);
      break;
    case GAS_DANGER:
      digitalWrite(RED_LED_PIN, HIGH);
      break;
  }
}

// Control active buzzer - tham khảo handleBuzzer từ code mẫu
void controlBuzzer(bool fireDetected, GasLevel gasLevel) {
  static unsigned long lastBuzzerTime = 0;
  static int buzzerCount = 0;
  static bool buzzerActive = false;
  unsigned long currentTime = millis();
  
  // Logic tương tự handleBuzzer trong code mẫu
  if (fireDetected) {
    // Phát hiện lửa: 10 tiếng beep liên tiếp
    if (!buzzerActive || (currentTime - lastBuzzerTime >= 500)) {
      if (buzzerCount < 20) { // 10 lần ON/OFF = 20 states
        digitalWrite(BUZZER_SIGNAL_PIN, (buzzerCount % 2 == 0) ? HIGH : LOW);
        buzzerCount++;
        lastBuzzerTime = currentTime;
        if (buzzerCount == 1) buzzerActive = true;
      } else {
        buzzerCount = 0;
        buzzerActive = false;
        digitalWrite(BUZZER_SIGNAL_PIN, LOW);
      }
    }
  } 
  else if (gasLevel == GAS_DANGER || gasLevel == GAS_WARNING) {
    // Phát hiện gas: 10 tiếng beep liên tiếp tương tự fire
    if (!buzzerActive || (currentTime - lastBuzzerTime >= 500)) {
      if (buzzerCount < 20) { // 10 lần ON/OFF
        digitalWrite(BUZZER_SIGNAL_PIN, (buzzerCount % 2 == 0) ? HIGH : LOW);
        buzzerCount++;
        lastBuzzerTime = currentTime;
        if (buzzerCount == 1) buzzerActive = true;
      } else {
        buzzerCount = 0;
        buzzerActive = false;
        digitalWrite(BUZZER_SIGNAL_PIN, LOW);
      }
    }
  } 
  else {
    // An toàn: Tắt buzzer
    digitalWrite(BUZZER_SIGNAL_PIN, LOW);
    buzzerCount = 0;
    buzzerActive = false;
  }
}

// Convert gas level to string
String gasLevelToString(GasLevel level) {
  switch (level) {
    case GAS_SAFE: return "SAFE";
    case GAS_WARNING: return "WARNING";
    case GAS_DANGER: return "DANGER";
    default: return "UNKNOWN";
  }
}

// Read data from all sensors
SensorData readSensorData() {
  SensorData data;
  
  // Read temperature and humidity
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Read MQ gas sensor (both analog and digital)
  int gasAnalog;
  bool gasDigital;
  GasLevel gasLevel = readGasLevel(&gasAnalog, &gasDigital);
  data.gasAnalog = gasAnalog;
  data.gasDigital = gasDigital;
  data.gasStatus = gasLevelToString(gasLevel);
  
  // Read fire sensor
  data.fireDetected = readFireSensor();
  
  // Check if readings are valid
  if (isnan(data.temperature) || isnan(data.humidity)) {
    data.isValid = false;
    Serial.println("Failed to read from DHT sensor!");
  } else {
    data.isValid = true;
  }
  
  // Control hardware based on sensor readings
  controlLEDs(gasLevel);
  controlBuzzer(data.fireDetected, gasLevel);
  
  return data;
}

// Display sensor data on Serial Monitor - thêm debug gas digital như code mẫu
void displaySensorData(const SensorData& data) {
  if (data.isValid) {
    Serial.println("===== ESP32 SENSOR READINGS =====");
    Serial.print("Temperature: ");
    Serial.print(data.temperature);
    Serial.println(" *C");
    Serial.print("Humidity: ");
    Serial.print(data.humidity);
    Serial.println(" %");
    Serial.print("Gas Analog: ");
    Serial.print(data.gasAnalog);
    Serial.print("/4095 (Status: ");
    Serial.print(data.gasStatus);
    Serial.println(")");
    Serial.print("Gas Digital: ");
    Serial.println(data.gasDigital ? "TRIGGERED" : "NORMAL");
    Serial.print("Fire Detected: ");
    Serial.println(data.fireDetected ? "YES" : "NO");
    
    // Debug info tương tự code mẫu
    Serial.print("Debug - Gas Digital Raw: ");
    Serial.print(data.gasDigital);
    Serial.print(", Fire Raw: ");
    Serial.println(data.fireDetected);
    Serial.println("=================================");
  } else {
    Serial.println("Invalid sensor data");
  }
}

// ===== SECTION 3: WIFI CONNECTION MANAGEMENT =====

// Connect to WiFi network
bool connectWiFi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, wifi_password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected successfully");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println("\nWiFi connection failed");
    return false;
  }
}

// Check WiFi connection status
bool isWiFiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

// ===== SECTION 4: MQTT COMMUNICATION MODULE =====

// Connect to MQTT broker
bool connectMQTT() {
  if (!isWiFiConnected()) {
    Serial.println("WiFi not connected. Cannot connect to MQTT.");
    return false;
  }
  
  if (client.connect(clientID, mqtt_username, mqtt_password)) {
    Serial.println("Connected to MQTT Broker successfully!");
    return true;
  } else {
    Serial.print("MQTT connection failed, rc=");
    Serial.println(client.state());
    return false;
  }
}

// Check MQTT connection status
bool isMQTTConnected() {
  return client.connected();
}

// Publish data to MQTT topic with improved error handling
bool publishToMQTT(const char* topic, const String& payload) {
  // Ensure MQTT connection is active before publishing
  if (!isMQTTConnected()) {
    Serial.println("MQTT not connected during publish attempt");
    return false;
  }
  
  if (client.publish(topic, payload.c_str())) {
    Serial.print("Data sent to topic '");
    Serial.print(topic);
    Serial.print("': ");
    Serial.println(payload);
    return true;
  } else {
    Serial.print("Failed to send data to topic: ");
    Serial.println(topic);
    return false;
  }
}

// Send sensor data via MQTT
void sendSensorDataMQTT(const SensorData& data) {
  if (!data.isValid) {
    Serial.println("Cannot send invalid sensor data");
    return;
  }
  
  // Send temperature data
  String tempPayload = String(data.temperature);
  if (!publishToMQTT(temperature_topic, tempPayload)) {
    Serial.println("Failed to publish temperature data");
  }
  
  // Send humidity data
  String humPayload = String(data.humidity);
  if (!publishToMQTT(humidity_topic, humPayload)) {
    Serial.println("Failed to publish humidity data");
  }
  
  // Send gas analog reading
  String gasAnalogPayload = String(data.gasAnalog);
  if (!publishToMQTT(gas_analog_topic, gasAnalogPayload)) {
    Serial.println("Failed to publish gas analog data");
  }
  
  // Send gas digital state
  String gasDigitalPayload = data.gasDigital ? "TRIGGERED" : "NORMAL";
  if (!publishToMQTT(gas_digital_topic, gasDigitalPayload)) {
    Serial.println("Failed to publish gas digital data");
  }
  
  // Send gas status data
  if (!publishToMQTT(gas_status_topic, data.gasStatus)) {
    Serial.println("Failed to publish gas status data");
  }
  
  // Send fire detection data
  String firePayload = data.fireDetected ? "FIRE_DETECTED" : "NO_FIRE";
  if (!publishToMQTT(fire_topic, firePayload)) {
    Serial.println("Failed to publish fire detection data");
  }
}

// Disconnect from MQTT broker
void disconnectMQTT() {
  if (isMQTTConnected()) {
    client.disconnect();
    Serial.println("Disconnected from MQTT broker");
  }
}

// ===== SECTION 5: MAIN PROGRAM FLOW =====

void setup() {
  Serial.begin(115200);
  
  // Initialize sensor
  initSensor();
  
  // Connect to WiFi
  if (!connectWiFi()) {
    Serial.println("Cannot proceed without WiFi connection");
    while(1); // Stop execution
  }
  
  // Connect to MQTT broker
  if (!connectMQTT()) {
    Serial.println("Initial MQTT connection failed. Will retry in main loop.");
  }
  
  Serial.println("System initialized successfully");
}

void loop() {
  // Ensure WiFi connection is active
  if (!isWiFiConnected()) {
    Serial.println("WiFi disconnected. Reconnecting...");
    if (!connectWiFi()) {
      Serial.println("WiFi reconnection failed. Retrying in 5 seconds...");
      delay(5000);
      return; // Skip this loop iteration
    }
  }
  
  // Ensure MQTT connection is active
  if (!isMQTTConnected()) {
    Serial.println("MQTT disconnected. Reconnecting...");
    if (!connectMQTT()) {
      Serial.println("MQTT reconnection failed. Retrying in 5 seconds...");
      delay(5000);
      return; // Skip this loop iteration
    }
  }
  
  // Maintain MQTT connection (process incoming messages, keepalive)
  client.loop();
  
  // Read sensor data
  SensorData sensorData = readSensorData();
  
  // Display data locally
  displaySensorData(sensorData);
  
  // Send data via MQTT (only if valid data)
  if (sensorData.isValid) {
    sendSensorDataMQTT(sensorData);
  }
  
  // Wait before next reading (keep connection alive)
  delay(5000); // Wait 5 seconds before next reading
}

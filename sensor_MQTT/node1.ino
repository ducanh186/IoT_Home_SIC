/* 
 * ESP32 SAFETY MONITORING SYSTEM - REWRITTEN LOGIC
 * ESP32 NodeMCU + Raspberry Pi 5
 * 
 * MAIN FEATURES:
 * ✅ Temperature & Humidity monitoring (DHT11)
 * ✅ 3-level Gas detection with LED indicators (SAFE/WARNING/DANGER)
 * ✅ Fire detection with immediate alert
 * ✅ PWM-controlled buzzer for fire/gas alerts
 * ✅ MQTT communication to Raspberry Pi 5
 * ✅ Auto WiFi reconnection & error handling
 * 
 * HARDWARE CONFIGURATION:
 * - DHT11: GPIO 4 (Temperature & Humidity)
 * - MQ Gas Sensor: GPIO 34 (Analog) + GPIO 35 (Digital)
 * - Flame Sensor: GPIO 26 (Digital fire detection)
 * - Green LED: GPIO 18 (Gas SAFE)
 * - Yellow LED: GPIO 19 (Gas WARNING) 
 * - Red LED: GPIO 21 (Gas DANGER)
 * - Buzzer: GPIO 5 (PWM controlled)
 * 
 * GAS LEVELS & LED LOGIC:
 * - SAFE (0-1400): Green LED ON
 * - WARNING (1400-1600): Yellow LED ON + Buzzer PWM
 * - DANGER (1600+): Red LED ON + Buzzer PWM
 * 
 * FIRE DETECTION:
 * - Fire detected: All 3 LEDs flash continuously + Buzzer PWM alert
 */

#include "DHT.h"
#include "PubSubClient.h"
#include "WiFi.h"
#include <Wire.h>

// ===== HARDWARE CONFIGURATION =====
#define DHTPIN 4                 // DHT11 data pin
#define DHTTYPE DHT11            // DHT sensor type
DHT dht(DHTPIN, DHTTYPE);

// MQ Gas Sensor Configuration
#define MQ_ANALOG_PIN 34         // GPIO 34 (ADC) - Analog gas reading
#define MQ_DIGITAL_PIN 35        // GPIO 35 - Digital threshold detection
#define GAS_SAFE_THRESHOLD 1400  // Analog value: SAFE level (0-1400)
#define GAS_WARNING_THRESHOLD 1600 // Analog value: WARNING level (1400-1600)
// Above 1900 = DANGER level

// Fire Sensor Configuration  
#define FIRE_SENSOR_PIN 26       // GPIO 26 - Digital fire detection

// LED Status Indicators
#define GREEN_LED_PIN 18         // GPIO 18 - Gas SAFE status
#define YELLOW_LED_PIN 19        // GPIO 19 - Gas WARNING status  
#define RED_LED_PIN 21           // GPIO 21 - Gas DANGER status

// PWM Buzzer Configuration
#define BUZZER_PIN 5             // GPIO 5 - PWM buzzer control
#define BUZZER_CHANNEL 0         // PWM channel for buzzer
#define BUZZER_FREQUENCY 2000    // PWM frequency (2kHz)
#define BUZZER_RESOLUTION 8      // PWM resolution (8-bit: 0-255)

// WiFi Configuration
const char* ssid = "VIETTEL";                
const char* wifi_password = "12345678";

// MQTT Configuration
const char* mqtt_server = "192.168.1.3";
const char* mqtt_username = "pi101";
const char* mqtt_password = "1234";
const char* clientID = "ESP32_Safety_Monitor";

// MQTT Topics
const char* temperature_topic = "temperature";
const char* humidity_topic = "humidity";
const char* gas_analog_topic = "gas_analog";
const char* gas_digital_topic = "gas_digital";
const char* gas_status_topic = "gas_status";
const char* fire_topic = "fire_detected";

// WiFi and MQTT objects
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient);

// Gas level enumeration
enum GasLevel {
  GAS_SAFE,     // 0-1400: Green LED
  GAS_WARNING,  // 1400-1600: Yellow LED + Buzzer
  GAS_DANGER    // 1600+: Red LED + Buzzer
};

// System data structure
struct SystemData {
  float temperature;
  float humidity;
  int gasAnalogValue;      // 0-4095 ADC reading
  bool gasDigitalTriggered; // Digital threshold status
  GasLevel gasLevel;       // Current gas safety level
  bool fireDetected;       // Fire sensor status
  bool isDataValid;        // Sensor reading validity
};

// ===== SYSTEM INITIALIZATION =====
void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32 Safety Monitoring System Starting...");
  
  // Initialize hardware components
  initializeHardware();
  
  // Connect to WiFi
  if (!connectToWiFi()) {
    Serial.println("❌ Cannot proceed without WiFi connection");
    while(1) delay(1000); // Halt system
  }
  
  // Connect to MQTT broker
  if (!connectToMQTT()) {
    Serial.println("⚠️ Initial MQTT connection failed. Will retry in main loop.");
  }
  
  Serial.println("✅ System initialization complete!");
  Serial.println("📊 Starting sensor monitoring...\n");
}

// ===== MAIN PROGRAM LOOP =====
void loop() {
  // Ensure connections are active
  maintainConnections();
  
  // Read all sensor data
  SystemData systemData = readAllSensors();
  
  // Control hardware based on readings
  controlLEDIndicators(systemData.gasLevel, systemData.fireDetected);
  controlPWMBuzzer(systemData.fireDetected, systemData.gasLevel);
  
  // Display readings on Serial Monitor
  displaySensorReadings(systemData);
  
  // Send data via MQTT
  if (systemData.isDataValid) {
    sendDataToMQTT(systemData);
  }
  
  // Wait before next reading
  delay(2000);
}
// ===== HARDWARE INITIALIZATION =====
void initializeHardware() {
  Serial.println("🔧 Initializing hardware components...");
  
  // Initialize DHT11 temperature & humidity sensor
  dht.begin();
  Serial.println("  ✅ DHT11 sensor (GPIO 4) - Temperature & Humidity");
  
  // Initialize MQ gas sensor pins
  pinMode(MQ_ANALOG_PIN, INPUT);
  pinMode(MQ_DIGITAL_PIN, INPUT);
  Serial.println("  ✅ MQ Gas sensor - Analog (GPIO 34) + Digital (GPIO 35)");
  
  // Initialize fire sensor
  pinMode(FIRE_SENSOR_PIN, INPUT);
  Serial.println("  ✅ Flame sensor (GPIO 26) - Fire detection");
  
  // Initialize LED indicator pins
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  Serial.println("  ✅ LED indicators (GPIO 18,19,21) - Status display");
  
  // Initialize PWM buzzer (compatible with ESP32 Core 2.x and 3.x)
  pinMode(BUZZER_PIN, OUTPUT);
  
  #if ESP_ARDUINO_VERSION_MAJOR >= 3
    // ESP32 Arduino Core 3.0+ syntax
    ledcAttach(BUZZER_PIN, BUZZER_FREQUENCY, BUZZER_RESOLUTION);
    ledcWrite(BUZZER_PIN, 0); // Ensure buzzer is off
  #else
    // ESP32 Arduino Core 2.x syntax
    ledcSetup(BUZZER_CHANNEL, BUZZER_FREQUENCY, BUZZER_RESOLUTION);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHANNEL);
    ledcWrite(BUZZER_CHANNEL, 0); // Ensure buzzer is off
  #endif
  
  Serial.println("  ✅ PWM Buzzer (GPIO 5) - Audio alerts");
  
  // Test all LEDs
  testSystemLEDs();
  Serial.println("🔧 Hardware initialization complete!");
}

// Test LED functionality at startup
void testSystemLEDs() {
  Serial.println("  🔍 Testing LED system...");
  
  // Test each LED for 200ms
  digitalWrite(GREEN_LED_PIN, HIGH);
  delay(200);
  digitalWrite(GREEN_LED_PIN, LOW);
  
  digitalWrite(YELLOW_LED_PIN, HIGH);
  delay(200);
  digitalWrite(YELLOW_LED_PIN, LOW);
  
  digitalWrite(RED_LED_PIN, HIGH);
  delay(200);
  digitalWrite(RED_LED_PIN, LOW);
  
  Serial.println("  ✅ LED test completed");
}

// ===== SENSOR READING FUNCTIONS =====
SystemData readAllSensors() {
  SystemData data;
  
  // Read temperature and humidity from DHT11
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Validate DHT readings
  if (isnan(data.temperature) || isnan(data.humidity)) {
    data.isDataValid = false;
    Serial.println("❌ DHT11 sensor reading failed!");
    return data;
  }
  
  // Read MQ gas sensor (analog + digital)
  data.gasAnalogValue = analogRead(MQ_ANALOG_PIN);
  data.gasDigitalTriggered = (digitalRead(MQ_DIGITAL_PIN) == LOW);
  
  // Determine gas safety level based on analog reading
  if (data.gasAnalogValue < GAS_SAFE_THRESHOLD) {
    data.gasLevel = GAS_SAFE;
  } else if (data.gasAnalogValue < GAS_WARNING_THRESHOLD) {
    data.gasLevel = GAS_WARNING;
  } else {
    data.gasLevel = GAS_DANGER;
  }
  
  // Read fire sensor (digital)
  data.fireDetected = (digitalRead(FIRE_SENSOR_PIN) == HIGH);
  
  data.isDataValid = true;
  return data;
}

// ===== LED CONTROL LOGIC =====
void controlLEDIndicators(GasLevel gasLevel, bool fireDetected) {
  static unsigned long lastLEDFlash = 0;
  static bool ledFlashState = false;
  unsigned long currentTime = millis();
  
  // Fire detection: All LEDs flash continuously
  if (fireDetected) {
    if (currentTime - lastLEDFlash >= 200) { // Flash every 200ms
      ledFlashState = !ledFlashState;
      
      // All LEDs flash together
      digitalWrite(GREEN_LED_PIN, ledFlashState ? HIGH : LOW);
      digitalWrite(YELLOW_LED_PIN, ledFlashState ? HIGH : LOW);
      digitalWrite(RED_LED_PIN, ledFlashState ? HIGH : LOW);
      
      lastLEDFlash = currentTime;
    }
  }
  // Normal gas level indication (no fire)
  else {
    // Turn off all LEDs first
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(YELLOW_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, LOW);
    
    // Turn on appropriate LED based on gas level
    switch (gasLevel) {
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
}

// ===== PWM BUZZER CONTROL LOGIC =====
// Buzzer tone patterns for different alert types
void playBuzzerTone(int intensity, bool enable) {
  if (enable) {
    #if ESP_ARDUINO_VERSION_MAJOR >= 3
      ledcWrite(BUZZER_PIN, intensity); // ESP32 Core 3.0+ - PHÁT ÂM THANH
    #else
      ledcWrite(BUZZER_CHANNEL, intensity); // ESP32 Core 2.x - PHÁT ÂM THANH
    #endif
  } else {
    #if ESP_ARDUINO_VERSION_MAJOR >= 3
      ledcWrite(BUZZER_PIN, 0); // ESP32 Core 3.0+ - TẮT ÂM THANH
    #else
      ledcWrite(BUZZER_CHANNEL, 0); // ESP32 Core 2.x - TẮT ÂM THANH
    #endif
  }
}

void controlPWMBuzzer(bool fireDetected, GasLevel gasLevel) {
  static unsigned long lastBuzzerUpdate = 0;
  static bool buzzerState = false;
  unsigned long currentTime = millis();
  
  // Fire detection: Continuous high-frequency beeping
  if (fireDetected) {
    if (currentTime - lastBuzzerUpdate >= 150) { // 150ms intervals
      buzzerState = !buzzerState;
      playBuzzerTone(200, buzzerState); // High intensity fire alert
      lastBuzzerUpdate = currentTime;
    }
  }
  // Gas warning/danger: Slower beeping pattern
  else if (gasLevel == GAS_WARNING || gasLevel == GAS_DANGER) {
    unsigned int beepInterval = (gasLevel == GAS_DANGER) ? 500 : 1000; // Faster for danger
    unsigned int pwmIntensity = (gasLevel == GAS_DANGER) ? 180 : 120;   // Louder for danger
    
    if (currentTime - lastBuzzerUpdate >= beepInterval) {
      buzzerState = !buzzerState;
      playBuzzerTone(pwmIntensity, buzzerState); // Variable intensity based on gas level
      lastBuzzerUpdate = currentTime;
    }
  }
  // Safe condition: Turn off buzzer
  else {
    playBuzzerTone(0, false); // TẮT BUZZER KHI AN TOÀN
    buzzerState = false;
  }
}

// ===== DISPLAY & MONITORING =====
void displaySensorReadings(const SystemData& data) {
  if (!data.isDataValid) {
    Serial.println("❌ Invalid sensor data - Skipping display");
    return;
  }
  
  Serial.println("╔═══════════════════════════════════════════════════════╗");
  Serial.println("║            🏠 ESP32 SAFETY MONITORING SYSTEM          ║");
  Serial.println("╠═══════════════════════════════════════════════════════╣");
  
  // Temperature & Humidity
  Serial.printf("║ 🌡️  Temperature: %6.1f°C                            ║\n", data.temperature);
  Serial.printf("║ 💧 Humidity:    %6.1f%%                             ║\n", data.humidity);
  
  // Gas sensor readings
  Serial.printf("║ 💨 Gas Analog:  %4d/4095                           ║\n", data.gasAnalogValue);
  Serial.printf("║ 🔘 Gas Digital: %-9s                           ║\n", 
                data.gasDigitalTriggered ? "TRIGGERED" : "NORMAL");
  
  // Gas safety level with visual indicators
  const char* gasStatusText;
  const char* gasIcon;
  switch (data.gasLevel) {
    case GAS_SAFE:
      gasStatusText = "SAFE";
      gasIcon = "🟢";
      break;
    case GAS_WARNING:
      gasStatusText = "WARNING";
      gasIcon = "🟡";
      break;
    case GAS_DANGER:
      gasStatusText = "DANGER";
      gasIcon = "🔴";
      break;
  }
  Serial.printf("║ %s Gas Level:   %-9s                          ║\n", gasIcon, gasStatusText);
  
  // Fire detection
  Serial.printf("║ 🔥 Fire Status: %-9s                           ║\n", 
                data.fireDetected ? "DETECTED" : "NO FIRE");
  
  // Alert status
  if (data.fireDetected) {
    Serial.println("║ 🚨🔥 FIRE EMERGENCY - ALL LEDS FLASHING! 🔥🚨       ║");
  } else if (data.gasLevel == GAS_DANGER) {
    Serial.println("║ ⚠️🚨  GAS DANGER ALERT - EVACUATE AREA!  🚨⚠️       ║");
  } else if (data.gasLevel == GAS_WARNING) {
    Serial.println("║ ⚠️⚠️  GAS WARNING - CHECK VENTILATION  ⚠️⚠️        ║");
  } else {
    Serial.println("║ ✅✅ All systems normal - Environment safe ✅✅     ║");
  }
  
  Serial.println("╚═══════════════════════════════════════════════════════╝");
  Serial.println();
}

// Convert gas level to string for MQTT
String gasLevelToString(GasLevel level) {
  switch (level) {
    case GAS_SAFE: return "SAFE";
    case GAS_WARNING: return "WARNING"; 
    case GAS_DANGER: return "DANGER";
    default: return "UNKNOWN";
  }
}

// ===== WIFI CONNECTION MANAGEMENT =====
bool connectToWiFi() {
  Serial.print("📡 Connecting to WiFi network: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, wifi_password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.print("📍 IP Address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    return false;
  }
}

bool isWiFiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

// ===== MQTT COMMUNICATION =====
bool connectToMQTT() {
  if (!isWiFiConnected()) {
    Serial.println("❌ WiFi not connected. Cannot connect to MQTT.");
    return false;
  }
  
  Serial.print("📡 Connecting to MQTT broker: ");
  Serial.println(mqtt_server);
  
  if (client.connect(clientID, mqtt_username, mqtt_password)) {
    Serial.println("✅ Connected to MQTT broker successfully!");
    return true;
  } else {
    Serial.print("❌ MQTT connection failed, error code: ");
    Serial.println(client.state());
    return false;
  }
}

bool isMQTTConnected() {
  return client.connected();
}

// Maintain WiFi and MQTT connections
void maintainConnections() {
  // Check and reconnect WiFi if needed
  if (!isWiFiConnected()) {
    Serial.println("⚠️ WiFi disconnected. Reconnecting...");
    if (!connectToWiFi()) {
      Serial.println("❌ WiFi reconnection failed. Retrying in next loop...");
      delay(5000);
      return;
    }
  }
  
  // Check and reconnect MQTT if needed
  if (!isMQTTConnected()) {
    Serial.println("⚠️ MQTT disconnected. Reconnecting...");
    if (!connectToMQTT()) {
      Serial.println("❌ MQTT reconnection failed. Retrying in next loop...");
      delay(5000);
      return;
    }
  }
  
  // Maintain MQTT connection
  client.loop();
}

// Send sensor data via MQTT
void sendDataToMQTT(const SystemData& data) {
  if (!isMQTTConnected()) {
    Serial.println("❌ MQTT not connected. Cannot send data.");
    return;
  }
  
  // Send temperature
  String tempStr = String(data.temperature, 1);
  if (client.publish(temperature_topic, tempStr.c_str())) {
    Serial.printf("📤 Sent temperature: %s°C\n", tempStr.c_str());
  }
  
  // Send humidity
  String humStr = String(data.humidity, 1);
  if (client.publish(humidity_topic, humStr.c_str())) {
    Serial.printf("📤 Sent humidity: %s%%\n", humStr.c_str());
  }
  
  // Send gas analog value
  String gasAnalogStr = String(data.gasAnalogValue);
  if (client.publish(gas_analog_topic, gasAnalogStr.c_str())) {
    Serial.printf("📤 Sent gas analog: %s\n", gasAnalogStr.c_str());
  }
  
  // Send gas digital status
  String gasDigitalStr = data.gasDigitalTriggered ? "TRIGGERED" : "NORMAL";
  if (client.publish(gas_digital_topic, gasDigitalStr.c_str())) {
    Serial.printf("📤 Sent gas digital: %s\n", gasDigitalStr.c_str());
  }
  
  // Send gas safety level
  String gasStatusStr = gasLevelToString(data.gasLevel);
  if (client.publish(gas_status_topic, gasStatusStr.c_str())) {
    Serial.printf("📤 Sent gas status: %s\n", gasStatusStr.c_str());
  }
  
  // Send fire detection status
  String fireStr = data.fireDetected ? "FIRE_DETECTED" : "NO_FIRE";
  if (client.publish(fire_topic, fireStr.c_str())) {
    Serial.printf("📤 Sent fire status: %s\n", fireStr.c_str());
  }
}

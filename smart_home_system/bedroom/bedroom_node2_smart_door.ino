/*
 * BEDROOM NODE 2 - Smart Door Controller
 * ESP32 + Servo + IR Sensor
 * 
 * CHỨC NĂNG:
 * ✅ Tự động mở cửa khi phát hiện người
 * ✅ Tự động đóng cửa sau thời gian timeout
 * ✅ Điều khiển thủ công qua MQTT/Web dashboard
 * ✅ Smooth servo movement
 * ✅ Real-time status reporting
 * ✅ Sử dụng hostname cho MQTT
 * 
 * HARDWARE CONFIGURATION:
 * - Servo SG90: GPIO 18
 * - IR Sensor ARD2-2233: GPIO 16 (OUT pin)
 * 
 * MQTT TOPICS:
 * - home/bedroom/node2/door/status (publish)
 * - home/bedroom/node2/door/command (subscribe)
 * - home/bedroom/node2/ir_sensor/value (publish)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// ===== NETWORK CONFIGURATION =====
const char* WIFI_SSID = "SSIoT-02";
const char* WIFI_PASSWORD = "SSIoT-02";

// ===== MQTT BROKER CONFIGURATION =====
const char* MQTT_SERVER = "pi101.local";  // hostname thay vì IP
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "pi101";
const char* MQTT_PASSWORD = "1234";

// Backup IP nếu hostname không hoạt động
const char* MQTT_SERVER_IP = "192.168.1.3";

// ===== MQTT TOPICS =====
const char* BEDROOM_NODE2_DOOR_STATUS_TOPIC = "home/bedroom/node2/door/status";
const char* BEDROOM_NODE2_DOOR_CMD_TOPIC = "home/bedroom/node2/door/command";
const char* BEDROOM_NODE2_IR_SENSOR_TOPIC = "home/bedroom/node2/ir_sensor/value";
const char* SYSTEM_HEARTBEAT_TOPIC = "home/system/heartbeat";
const char* SYSTEM_STATUS_TOPIC = "home/system/status";

// ===== CLIENT ID =====
const char* CLIENT_ID = "ESP32_Bedroom_Node2_Door";

// ===== TIMING CONSTANTS =====
const unsigned long MQTT_RECONNECT_DELAY = 5000;   // 5 seconds
const unsigned long HEARTBEAT_INTERVAL = 30000;    // 30 seconds
const unsigned long SENSOR_READ_INTERVAL = 500;    // 500ms

// ===== HARDWARE PINS =====
#define SERVO_PIN 18
#define IR_SENSOR_PIN 16

// ===== SERVO SETTINGS =====
#define DOOR_CLOSED 0      // 0° = cửa đóng
#define DOOR_OPEN 90       // 90° = cửa mở
#define SMOOTH_DELAY 20    // ms delay between steps

// ===== TIMING SETTINGS =====
#define PRESENCE_TIMEOUT 20000    // 20 giây không người → đóng cửa
#define MANUAL_OVERRIDE 60000     // 60 giây override sau lệnh thủ công

// ===== GLOBAL VARIABLES =====
WiFiClient espClient;
PubSubClient client(espClient);
Servo doorServo;

// State variables
int currentAngle = DOOR_CLOSED;
bool doorState = false;  // false = closed, true = open
bool presenceDetected = false;
unsigned long lastPersonSeen = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastSensorRead = 0;
unsigned long manualOverrideUntil = 0;
unsigned long lastMQTTAttempt = 0;
String lastAction = "system_start";

// ===== SETUP FUNCTION =====
void setup() {
  Serial.begin(115200);
  Serial.println("\n🚪 BEDROOM NODE 2 - Smart Door Controller Starting...");
  
  initializeHardware();
  connectToWiFi();
  setupMQTT();
  
  Serial.println("✅ Bedroom Node 2 initialized successfully!");
  Serial.println("🚪 Smart door system ready...\n");
}

// ===== MAIN LOOP =====
void loop() {
  maintainConnections();
  
  if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readSensorData();
    lastSensorRead = millis();
  }
  
  checkAutomaticControl();
  
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    publishHeartbeat();
    lastHeartbeat = millis();
  }
  
  client.loop();
  delay(50);
}

// ===== HARDWARE INITIALIZATION =====
void initializeHardware() {
  Serial.println("🔧 Initializing hardware...");
  
  // IR Sensor
  pinMode(IR_SENSOR_PIN, INPUT);
  Serial.println("  ✅ IR Sensor (GPIO 16)");
  
  // Servo
  doorServo.attach(SERVO_PIN);
  doorServo.write(DOOR_CLOSED);
  currentAngle = DOOR_CLOSED;
  Serial.println("  ✅ Servo SG90 (GPIO 18) - Position: 0° (closed)");
  
  delay(1000); // Allow servo to reach position
}

// ===== WIFI CONNECTION =====
void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi connection failed!");
  }
}

// ===== MQTT SETUP =====
void setupMQTT() {
  // Thử kết nối với hostname trước
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(mqttCallback);
  
  if (!connectToMQTT()) {
    // Nếu hostname không hoạt động, thử IP backup
    Serial.println("⚠️ Hostname failed, trying backup IP...");
    client.setServer(MQTT_SERVER_IP, MQTT_PORT);
    connectToMQTT();
  }
}

bool connectToMQTT() {
  if (WiFi.status() != WL_CONNECTED) return false;
  
  Serial.print("📡 Connecting to MQTT broker...");
  
  if (client.connect(CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
    Serial.println(" ✅ Connected!");
    
    // Subscribe to command topic
    client.subscribe(BEDROOM_NODE2_DOOR_CMD_TOPIC);
    Serial.printf("📥 Subscribed to: %s\n", BEDROOM_NODE2_DOOR_CMD_TOPIC);
    
    publishOnlineStatus();
    return true;
  } else {
    Serial.printf(" ❌ Failed, rc=%d\n", client.state());
    return false;
  }
}

void maintainConnections() {
  // Check WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi disconnected, reconnecting...");
    connectToWiFi();
    return;
  }
  
  // Check MQTT
  if (!client.connected() && millis() - lastMQTTAttempt >= MQTT_RECONNECT_DELAY) {
    Serial.println("⚠️ MQTT disconnected, reconnecting...");
    setupMQTT();
    lastMQTTAttempt = millis();
  }
}

// ===== SENSOR READING =====
void readSensorData() {
  // Read digital IR sensor (3-pin: VCC, GND, OUT)
  // Logic: LOW = có người, HIGH = không có người
  bool sensorReading = digitalRead(IR_SENSOR_PIN);
  bool currentPresence = !sensorReading; // Đảo ngược logic
  
  // Check for presence change
  if (currentPresence != presenceDetected) {
    presenceDetected = currentPresence;
    
    if (presenceDetected) {
      // Person detected
      lastPersonSeen = millis();
      Serial.println("👤 Person detected by IR sensor");
      
      publishSensorData();
      
      // Auto open door if closed and not in manual override
      if (!doorState && millis() > manualOverrideUntil) {
        Serial.println("🚪 Auto opening door for detected person");
        moveDoorTo(DOOR_OPEN, "auto_open");
      }
    } else {
      // Person no longer detected
      Serial.println("👤 Person no longer detected");
      publishSensorData();
    }
  }
}

void publishSensorData() {
  if (!client.connected()) return;
  
  StaticJsonDocument<150> doc;
  doc["presence"] = presenceDetected;
  doc["sensor_type"] = "IR_digital";
  doc["signal_strength"] = WiFi.RSSI();
  doc["timestamp"] = millis() / 1000;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(BEDROOM_NODE2_IR_SENSOR_TOPIC, jsonString.c_str());
}

// ===== AUTOMATIC CONTROL =====
void checkAutomaticControl() {
  // Skip if in manual override mode
  if (millis() < manualOverrideUntil) {
    return;
  }
  
  // Auto close door if no person detected for timeout
  if (doorState && !presenceDetected && 
      (millis() - lastPersonSeen) > PRESENCE_TIMEOUT) {
    Serial.println("🚪 Auto closing door - no person detected for timeout");
    moveDoorTo(DOOR_CLOSED, "auto_close");
  }
}

// ===== SERVO CONTROL =====
void moveDoorTo(int targetAngle, String action) {
  if (targetAngle < 0) targetAngle = 0;
  if (targetAngle > 90) targetAngle = 90;
  
  if (currentAngle == targetAngle) {
    Serial.println("🚪 Door already at target position");
    return;
  }
  
  Serial.printf("🚪 Moving door from %d° to %d° (%s)\n", currentAngle, targetAngle, action.c_str());
  lastAction = action;
  
  // Smooth movement
  int step = (targetAngle > currentAngle) ? 1 : -1;
  
  while (currentAngle != targetAngle) {
    currentAngle += step;
    doorServo.write(currentAngle);
    delay(SMOOTH_DELAY);
  }
  
  // Update door state
  doorState = (currentAngle > 45); // Consider open if > 45°
  
  Serial.printf("✅ Door movement complete: %d° (%s)\n", 
                currentAngle, doorState ? "OPEN" : "CLOSED");
  
  // Publish status
  publishDoorStatus();
}

// ===== MQTT CALLBACK =====
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.printf("📨 MQTT [%s]: %s\n", topic, message.c_str());
  
  if (String(topic) == BEDROOM_NODE2_DOOR_CMD_TOPIC) {
    handleDoorCommand(message);
  }
}

void handleDoorCommand(String jsonMessage) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, jsonMessage);
  
  if (error) {
    Serial.println("❌ JSON parsing failed");
    return;
  }
  
  String source = doc["source"] | "unknown";
  
  // Set manual override if command is from web/manual source
  if (source == "manual" || source == "web" || source == "button") {
    manualOverrideUntil = millis() + MANUAL_OVERRIDE;
    Serial.printf("🔧 Manual override activated for %d seconds\n", MANUAL_OVERRIDE/1000);
  }
  
  // Handle angle command
  if (doc.containsKey("angle")) {
    int targetAngle = doc["angle"];
    String action = "manual_" + String(targetAngle == DOOR_OPEN ? "open" : "close");
    moveDoorTo(targetAngle, action);
  }
  
  // Handle action command
  else if (doc.containsKey("action")) {
    String action = doc["action"];
    if (action == "open") {
      moveDoorTo(DOOR_OPEN, "manual_open");
    } else if (action == "close") {
      moveDoorTo(DOOR_CLOSED, "manual_close");
    } else if (action == "toggle") {
      int targetAngle = doorState ? DOOR_CLOSED : DOOR_OPEN;
      moveDoorTo(targetAngle, "manual_toggle");
    }
  }
}

// ===== MQTT PUBLISHING =====
void publishDoorStatus() {
  if (!client.connected()) return;
  
  StaticJsonDocument<300> doc;
  
  doc["angle"] = currentAngle;
  doc["state"] = doorState ? "open" : "closed";
  doc["presence"] = presenceDetected;
  doc["seconds_since_person"] = (millis() - lastPersonSeen) / 1000;
  doc["last_action"] = lastAction;
  doc["manual_override"] = (millis() < manualOverrideUntil);
  doc["override_remaining"] = manualOverrideUntil > millis() ? (manualOverrideUntil - millis()) / 1000 : 0;
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["timestamp"] = millis() / 1000;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(BEDROOM_NODE2_DOOR_STATUS_TOPIC, jsonString.c_str());
  Serial.println("📤 Door status published");
}

void publishHeartbeat() {
  if (!client.connected()) return;
  
  StaticJsonDocument<200> doc;
  doc["room"] = "bedroom";
  doc["node"] = "node2";
  doc["type"] = "smart_door";
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["door_state"] = doorState ? "open" : "closed";
  doc["presence"] = presenceDetected;
  doc["timestamp"] = millis() / 1000;
  
  String heartbeat;
  serializeJson(doc, heartbeat);
  client.publish(SYSTEM_HEARTBEAT_TOPIC, heartbeat.c_str());
}

void publishOnlineStatus() {
  if (!client.connected()) return;
  
  StaticJsonDocument<150> doc;
  doc["room"] = "bedroom";
  doc["node"] = "node2";
  doc["status"] = "online";
  doc["ip"] = WiFi.localIP().toString();
  doc["door_state"] = doorState ? "open" : "closed";
  doc["timestamp"] = millis() / 1000;
  
  String status;
  serializeJson(doc, status);
  client.publish(SYSTEM_STATUS_TOPIC, status.c_str());
}

#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "VIETTEL";
const char* password = "12345678";

// MQTT Broker settings
const char* mqtt_broker = "10.189.169.194";  // Raspberry Pi IP
const int mqtt_port = 1883;
const char* mqtt_username = "pi";
const char* mqtt_password = "1234";

// MQTT Topics
const char* servo_cmd_topic = "home/servo/cmd";
const char* servo_status_topic = "home/servo/status";

// Servo settings
#define SERVO_PIN 18
Servo myServo;
int currentAngle = 90;  // Default position
int minAngle = 0;
int maxAngle = 180;

// WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

// Status variables
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 30000; // 30 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize servo
  myServo.attach(SERVO_PIN);
  myServo.write(currentAngle);
  delay(500);
  
  Serial.println("ESP32 Servo MQTT Controller Starting...");
  
  // Connect to WiFi
  setupWiFi();
  
  // Setup MQTT
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);
  
  // Connect to MQTT broker
  connectMQTT();
  
  Serial.println("System ready!");
  publishStatus("ready");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();
  
  // Send heartbeat
  if (millis() - lastHeartbeat > heartbeatInterval) {
    publishHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(100);
}

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    String clientId = "ESP32_Servo_" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("connected");
      
      // Subscribe to servo command topic
      client.subscribe(servo_cmd_topic);
      Serial.print("Subscribed to: ");
      Serial.println(servo_cmd_topic);
      
      // Publish connection status
      publishStatus("connected");
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);
  
  // Handle servo command
  if (String(topic) == servo_cmd_topic) {
    handleServoCommand(message);
  }
}

void handleServoCommand(String command) {
  // Parse JSON command
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, command);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    publishStatus("error: invalid json");
    return;
  }
  
  // Extract angle from JSON
  if (doc.containsKey("angle")) {
    int targetAngle = doc["angle"];
    
    // Validate angle range
    if (targetAngle < minAngle || targetAngle > maxAngle) {
      Serial.println("Angle out of range!");
      publishStatus("error: angle out of range");
      return;
    }
    
    // Move servo smoothly
    moveServoSmooth(targetAngle);
    
    // Update current angle
    currentAngle = targetAngle;
    
    // Publish status
    publishAngleStatus();
    
    Serial.print("Servo moved to: ");
    Serial.println(currentAngle);
  }
  
  // Handle preset positions
  if (doc.containsKey("preset")) {
    String preset = doc["preset"];
    int targetAngle;
    
    if (preset == "home") {
      targetAngle = 90;
    } else if (preset == "left") {
      targetAngle = 0;
    } else if (preset == "right") {
      targetAngle = 180;
    } else {
      publishStatus("error: unknown preset");
      return;
    }
    
    moveServoSmooth(targetAngle);
    currentAngle = targetAngle;
    publishAngleStatus();
    
    Serial.print("Servo moved to preset '");
    Serial.print(preset);
    Serial.print("': ");
    Serial.println(currentAngle);
  }
}

void moveServoSmooth(int targetAngle) {
  int steps = abs(targetAngle - currentAngle);
  int stepDelay = 15; // ms between steps
  
  if (steps > 0) {
    int direction = (targetAngle > currentAngle) ? 1 : -1;
    
    for (int i = 0; i < steps; i++) {
      currentAngle += direction;
      myServo.write(currentAngle);
      delay(stepDelay);
    }
  }
}

void publishStatus(String status) {
  StaticJsonDocument<200> doc;
  doc["status"] = status;
  doc["timestamp"] = millis();
  doc["ip"] = WiFi.localIP().toString();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(servo_status_topic, jsonString.c_str());
}

void publishAngleStatus() {
  StaticJsonDocument<200> doc;
  doc["angle"] = currentAngle;
  doc["status"] = "moved";
  doc["timestamp"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(servo_status_topic, jsonString.c_str());
}

void publishHeartbeat() {
  StaticJsonDocument<200> doc;
  doc["heartbeat"] = true;
  doc["angle"] = currentAngle;
  doc["uptime"] = millis();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(servo_status_topic, jsonString.c_str());
}

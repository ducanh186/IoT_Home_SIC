/* 
 * NODE 1 - Environmental & Fire Safety Monitoring System
 * 
 * Features:
 * - Temperature & Humidity monitoring using DHT11 sensor (IMPLEMENTED)
 * - Fire detection using flame sensor (TODO)
 * - Buzzer alert system for fire warnings (TODO)
 * - Real-time data transmission via MQTT to Raspberry Pi 5
 * - WiFi connectivity with auto-reconnection
 * - Robust error handling and sensor validation
 * 
 * Current Status: Temperature/Humidity monitoring operational
 * Pending: Fire detection and buzzer alert integration
 */

#include "DHT.h"
#include "PubSubClient.h"
#include "WiFi.h"

// ===== SECTION 1: CONFIGURATION AND DECLARATIONS =====
// DHT Sensor Configuration
#define DHTPIN 4 
#define DHTTYPE DHT11 
DHT dht(DHTPIN, DHTTYPE);

// WiFi Configuration
const char* ssid = "VIETTEL";                
const char* wifi_password = "12345678";

// MQTT Configuration
const char* mqtt_server = "192.168.1.3"; // IP address of Raspberry Pi 5
const char* humidity_topic = "humidity"; // MQTT topic for humidity data
const char* temperature_topic = "temperature"; // MQTT topic for temperature data
const char* mqtt_username = "pi101"; // MQTT username
const char* mqtt_password = "1234"; // MQTT password
const char* clientID = "Weather_Reporter"; // MQTT client ID

// Initialize WiFi and MQTT objects
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient);

// Sensor data structure
struct SensorData {
  float temperature;
  float humidity;
  bool isValid;
};

// ===== SECTION 2: SENSOR CONTROL LOGIC =====

// Initialize DHT sensor
void initSensor() {
  dht.begin();
  Serial.println("DHT sensor initialized");
}

// Read data from DHT sensor
SensorData readSensorData() {
  SensorData data;
  
  data.temperature = dht.readTemperature();
  data.humidity = dht.readHumidity();
  
  // Check if readings are valid
  if (isnan(data.temperature) || isnan(data.humidity)) {
    data.isValid = false;
    Serial.println("Failed to read from DHT sensor!");
  } else {
    data.isValid = true;
  }
  
  return data;
}

// Display sensor data on Serial Monitor
void displaySensorData(const SensorData& data) {
  if (data.isValid) {
    Serial.print("Temperature: ");
    Serial.print(data.temperature);
    Serial.println(" *C");
    Serial.print("Humidity: ");
    Serial.print(data.humidity);
    Serial.println(" %");
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

// Publish data to MQTT topic with retry mechanism
bool publishToMQTT(const char* topic, const String& payload) {
  if (!isMQTTConnected()) {
    Serial.println("MQTT not connected. Attempting to reconnect...");
    if (!connectMQTT()) {
      return false;
    }
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
    
    // Retry once
    delay(100);
    if (connectMQTT()) {
      return client.publish(topic, payload.c_str());
    }
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
  publishToMQTT(temperature_topic, tempPayload);
  
  // Send humidity data
  String humPayload = String(data.humidity);
  publishToMQTT(humidity_topic, humPayload);
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
  
  Serial.println("System initialized successfully");
}

void loop() {
  // Ensure connections are active
  if (!isWiFiConnected()) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectWiFi();
  }
  
  if (!isMQTTConnected()) {
    Serial.println("MQTT disconnected. Reconnecting...");
    connectMQTT();
  }
  
  // Read sensor data
  SensorData sensorData = readSensorData();
  
  // Display data locally
  displaySensorData(sensorData);
  
  // Send data via MQTT
  if (sensorData.isValid) {
    sendSensorDataMQTT(sensorData);
  }
  
  // Disconnect and wait
  disconnectMQTT();
  delay(5000); // Wait 5 seconds before next reading
}

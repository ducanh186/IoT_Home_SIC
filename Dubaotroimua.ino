#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ==== Cảm biến DHT11 ====
#define DHTPIN 17
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ==== Cảm biến nước và LED ====
#define WATER_SENSOR_PIN 15
#define GREEN_LED 4   // Sửa tên LED tại đây
bool lastWaterState = HIGH;

// ==== WiFi Configuration ====
const char* ssid = "B5 205";
const char* wifi_password = "Ktx2052023";

// ==== MQTT Configuration ====
const char* mqtt_server = "192.168.1.70";
const char* mqtt_username = "pi101";
const char* mqtt_password = "1234";
const char* clientID = "ESP32_Safety_Monitor";

// ==== MQTT Topics ====
const char* temperature_topic = "temperature";
const char* humidity_topic = "humidity";
const char* water_topic = "water_detected";
const char* rain_topic = "rain_alert";  // Thêm topic trời mưa

// ==== WiFi & MQTT ====
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient);

enum HumidityLevel {
  HUMIDITY_LOW,
  HUMIDITY_HIGH
};

struct SystemData {
  float temperature;
  float humidity;
  bool waterState;
  HumidityLevel humidityStatus;
  bool isDataValid;
};

SystemData data;

// ==== Hàm kết nối WiFi ====
void connectWiFi() {
  Serial.print("Đang kết nối WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, wifi_password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi đã kết nối!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ==== Hàm kết nối MQTT ====
void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Đang kết nối MQTT...");
    if (client.connect(clientID, mqtt_username, mqtt_password)) {
      Serial.println("✅ MQTT kết nối thành công");
    } else {
      Serial.print("❌ Lỗi MQTT: ");
      Serial.print(client.state());
      Serial.println(" → thử lại sau 5s");
      delay(5000);
    }
  }
}

// ==== SETUP ====
void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(WATER_SENSOR_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);          // Sử dụng GREEN_LED
  digitalWrite(GREEN_LED, LOW);        // Tắt LED ban đầu

  Serial.println("Khởi động hệ thống: DHT11 + Water Sensor + GREEN LED");

  connectWiFi();
  connectMQTT();
}

// ==== LOOP ====
void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();

  // --- Đọc DHT11 ---
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (!isnan(h) && !isnan(t)) {
    data.temperature = t;
    data.humidity = h;
    data.isDataValid = true;

    // Phân loại mức độ ẩm
    if (h < 80.0) {
      data.humidityStatus = HUMIDITY_LOW;
      digitalWrite(GREEN_LED, LOW);  // Ẩm thấp → bật LED (low là bật LED nếu dùng active-low)
    } else {
      data.humidityStatus = HUMIDITY_HIGH;
      digitalWrite(GREEN_LED, HIGH); // Ẩm cao → tắt LED
    }

    Serial.print("🌡️ Nhiệt độ: ");
    Serial.print(data.temperature);
    Serial.print(" °C\t💧 Độ ẩm: ");
    Serial.print(data.humidity);
    Serial.println(" %");

    // --- Gửi dữ liệu lên MQTT ---
    char tempStr[10];
    char humidStr[10];
    dtostrf(data.temperature, 1, 2, tempStr);
    dtostrf(data.humidity, 1, 2, humidStr);
    client.publish(temperature_topic, tempStr);
    client.publish(humidity_topic, humidStr);
  } else {
    data.isDataValid = false;
    Serial.println("⚠️ Không đọc được dữ liệu từ DHT11!");
  }

  // --- Đọc cảm biến nước ---
  data.waterState = digitalRead(WATER_SENSOR_PIN);
  if (data.waterState != lastWaterState) {
    if (data.waterState == HIGH) {
      Serial.println(">> CẢNH BÁO: Phát hiện nước! Bật LED.");
      digitalWrite(GREEN_LED, HIGH); // Cảnh báo nước → bật LED
    } else {
      Serial.println(">> An toàn: Không có nước. Tắt LED.");
      digitalWrite(GREEN_LED, LOW);
    }
    lastWaterState = data.waterState;

    // Gửi trạng thái nước lên MQTT
    const char* waterMsg = data.waterState == HIGH ? "Troi mua" : "Troi khong mua";
    client.publish(water_topic, waterMsg);
  }

  // --- Thông báo trời mưa lên topic rain_alert ---
  if (data.humidity > 80 || data.waterState == HIGH) {
    Serial.println("☔ Trời mưa (độ ẩm cao hoặc phát hiện nước)");
    client.publish(rain_topic, "Trời đang mưa");
  } else {
    client.publish(rain_topic, "Trời khô ráo");
  }

  delay(2000);
}

/*
 * DỰ ÁN THÙNG RÁC THÔNG MINH - CODE CHO ESP32
 * (Dựa trên khung sườn của code cảnh báo khí gas)
 *
 * MỤC TIÊU:
 * ✅ Đo khoảng cách từ cảm biến siêu âm.
 * ✅ Gửi dữ liệu khoảng cách qua MQTT.
 * ✅ Nhận lệnh từ MQTT để điều khiển động cơ servo.
 * ✅ Tự động kết nối lại WiFi và MQTT khi bị mất kết nối.
 *
 * CẤU HÌNH PHẦN CỨNG:
 * - Cảm biến siêu âm HC-SR04: Trig (GPIO 5), Echo (GPIO 18)
 * - Động cơ Servo: Dây tín hiệu (GPIO 2)
 *
 */

#include "PubSubClient.h"
#include "WiFi.h"
#include <ESP32Servo.h>

// ===== CẤU HÌNH PHẦN CỨNG =====
// Định nghĩa chân cho cảm biến siêu âm
#define TRIG_PIN 5
#define ECHO_PIN 18

// Định nghĩa chân cho động cơ Servo
#define SERVO_PIN 2

// Khởi tạo đối tượng Servo
Servo trashCanServo;

// ===== CẤU HÌNH WIFI =====
const char* ssid = "VIETTEL";
const char* wifi_password = "12345678";

// ===== CẤU HÌNH MQTT =====
const char* mqtt_server = "192.168.1.3";
const char* mqtt_username = "pi101";
const char* mqtt_password = "1234";
const char* clientID = "ESP32_Smart_Trash_Can";

// Các Topics MQTT cho dự án thùng rác
const char* command_topic = "smart_trash_can/command"; // Nhận lệnh mở/đóng nắp
const char* status_topic = "smart_trash_can/status"; // Gửi trạng thái nắp
const char* distance_topic = "smart_trash_can/distance"; // Gửi dữ liệu khoảng cách

// Đối tượng WiFi và MQTT
WiFiClient wifiClient;
PubSubClient client(wifiClient);

// ===== HÀM CALLBACK KHI NHẬN TIN NHẮN MQTT =====
// Hàm này sẽ được gọi khi ESP32 nhận được tin nhắn từ Broker
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("➡️ Message arrived on topic: ");
  Serial.println(topic);

  // Chuyển đổi payload thành chuỗi
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("Payload: ");
  Serial.println(message);

  // Xử lý lệnh
  if (String(topic) == command_topic) {
    if (message == "open") {
      Serial.println("Received command: OPEN lid");
      trashCanServo.write(120); // Mở nắp ở góc 120 độ
      delay(1000); // Giữ nắp mở trong 1 giây
      client.publish(status_topic, "Lid OPEN");
    } else if (message == "close") {
      Serial.println("Received command: CLOSE lid");
      trashCanServo.write(0); // Đóng nắp ở góc 0 độ
      client.publish(status_topic, "Lid CLOSED");
    }
  }
}

// ===== HÀM KẾT NỐI VÀ DUY TRÌ MQTT =====
bool connectToMQTT() {
  if (!WiFi.isConnected()) {
    Serial.println("❌ WiFi not connected. Cannot connect to MQTT.");
    return false;
  }
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback); // Thiết lập hàm callback

  Serial.print("📡 Connecting to MQTT broker: ");
  Serial.println(mqtt_server);
  
  if (client.connect(clientID, mqtt_username, mqtt_password)) {
    Serial.println("✅ Connected to MQTT broker successfully!");
    // Đăng ký (subscribe) vào topic nhận lệnh
    client.subscribe(command_topic);
    Serial.printf("✅ Subscribed to topic: %s\n", command_topic);
    return true;
  } else {
    Serial.print("❌ MQTT connection failed, error code: ");
    Serial.println(client.state());
    return false;
  }
}

void maintainConnections() {
  // Đảm bảo kết nối WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi disconnected. Reconnecting...");
    WiFi.begin(ssid, wifi_password);
    delay(5000);
  }

  // Đảm bảo kết nối MQTT
  if (!client.connected()) {
    Serial.println("⚠️ MQTT disconnected. Reconnecting...");
    if (!connectToMQTT()) {
      Serial.println("❌ MQTT reconnection failed. Retrying in next loop...");
      delay(5000);
      return;
    }
  }
  
  client.loop();
}

// ===== HÀM ĐỌC GIÁ TRỊ CẢM BIẾN SIÊU ÂM =====
long readDistance() {
  // Gửi xung kích hoạt
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Đọc thời gian của xung Echo
  long duration = pulseIn(ECHO_PIN, HIGH);
  
  // Tính khoảng cách (cm)
  long distance = duration * 0.0343 / 2;
  
  return distance;
}

// ===== KHỞI TẠO HỆ THỐNG =====
void setup() {
  Serial.begin(115200);
  Serial.println("🚀 Smart Trash Can System Starting...");
  
  // Khởi tạo các chân GPIO
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Khởi tạo Servo
  trashCanServo.attach(SERVO_PIN);
  trashCanServo.write(0); // Đóng nắp khi khởi động
  Serial.println("✅ Hardware initialized!");

  // Kết nối WiFi
  WiFi.begin(ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected!");
  Serial.print("📍 IP Address: ");
  Serial.println(WiFi.localIP());
  
  // Kết nối MQTT lần đầu
  connectToMQTT();
  
  Serial.println("✅ System initialization complete!");
  Serial.println("📊 Starting distance monitoring...\n");
}

// ===== VÒNG LẶP CHÍNH CỦA CHƯƠNG TRÌNH =====
void loop() {
  // Đảm bảo kết nối luôn hoạt động
  maintainConnections();

  // Đọc khoảng cách và gửi đi
  long distance = readDistance();
  
  if (distance > 0) { // Đảm bảo khoảng cách hợp lệ
    Serial.printf("📏 Distance: %ld cm\n", distance);
    client.publish(distance_topic, String(distance).c_str());
  } else {
    Serial.println("❌ Distance reading failed!");
  }

  // Logic tự động mở/đóng nắp
  // Ví dụ: Nếu vật thể ở gần (dưới 20cm), tự động mở nắp
  if (distance > 0 && distance < 20) {
    trashCanServo.write(120);
    client.publish(status_topic, "Lid OPEN (Auto)");
  } else {
    trashCanServo.write(0);
    client.publish(status_topic, "Lid CLOSED");
  }

  delay(1000); // Chờ 1 giây trước khi đọc lại
}

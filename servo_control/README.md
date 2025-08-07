# ESP32 Servo Control System

Hệ thống điều khiển servo SG90 từ xa thông qua MQTT với Raspberry Pi 5 làm server.

## Kiến trúc hệ thống

```
Trình duyệt  ⇆  Nginx/Node-RED Dashboard (Pi 5)  ⇆  Mosquitto (Pi 5)
                                                    ▲        │
                                                    │(sub/pub)
                                                ESP32 MQTT client
                                                    │
                                              PWM servo SG90
```

## Cách hoạt động của hệ thống

### 🔄 **Luồng dữ liệu điều khiển:**

1. **Người dùng thao tác trên Dashboard** (Web Browser)
   - Kéo thanh trượt góc từ 0-180°
   - Hoặc nhấn nút preset (Home/Left/Right)
   - Trình duyệt gửi request đến Node-RED

2. **Node-RED xử lý lệnh** (Raspberry Pi 5)
   - Nhận input từ dashboard UI
   - Chuyển đổi thành JSON format
   - Publish message lên MQTT broker

3. **MQTT Broker phân phối** (Mosquitto trên Pi 5)
   - Nhận message từ Node-RED
   - Chuyển tiếp đến ESP32 đã subscribe

4. **ESP32 nhận và thực thi** 
   - Subscribe topic `home/servo/cmd`
   - Parse JSON để lấy góc mong muốn
   - Điều khiển PWM để quay servo

5. **Feedback trạng thái**
   - ESP32 gửi status về MQTT
   - Dashboard cập nhật gauge hiển thị
   - LED indicator hiện trạng thái kết nối

### 🤖 **ESP32 làm gì:**

**Khởi tạo:**
- Kết nối WiFi với mạng "VIETTEL"
- Kết nối MQTT broker tại IP 10.189.169.194
- Subscribe topic `home/servo/cmd` để nhận lệnh
- Cài đặt servo ở vị trí mặc định 90°

**Nhận lệnh điều khiển:**
```cpp
// Ví dụ JSON nhận được:
{"angle": 45, "timestamp": 1691234567}
{"preset": "home", "timestamp": 1691234567}
```

**Xử lý lệnh:**
- Parse JSON để lấy góc (0-180°) hoặc preset
- Kiểm tra giới hạn an toàn
- Di chuyển servo từ từ (smooth movement)
- Gửi feedback về dashboard

**Gửi trạng thái:**
```cpp
// Status feedback:
{"angle": 45, "status": "moved", "timestamp": 1691234567}
{"heartbeat": true, "uptime": 12345, "free_heap": 85000}
```

### 🖥️ **Raspberry Pi 5 làm gì:**

**Mosquitto MQTT Broker:**
- Lắng nghe port 1883 cho MQTT connections
- Xác thực user/password (pi/1234)
- Nhận message từ Node-RED và chuyển đến ESP32
- Nhận status từ ESP32 và chuyển về Node-RED

**Node-RED Dashboard:**
- Tạo web interface với các UI elements:
  - Slider điều khiển góc
  - Buttons cho preset positions
  - Gauge hiển thị góc hiện tại
  - LED indicator trạng thái kết nối
- Xử lý logic chuyển đổi UI → MQTT
- Cập nhật real-time khi nhận feedback

**Nginx Web Server:**
- Reverse proxy cho Node-RED dashboard
- Cung cấp HTTPS security
- Load balancing và caching
- Serve static files

## Thành phần hệ thống

### 🎯 **Raspberry Pi 5 - Trung tâm điều khiển**
- **Mosquitto MQTT Broker**: Trung gian giao tiếp giữa dashboard và ESP32
- **Node-RED**: Tạo giao diện web và xử lý logic điều khiển
- **Nginx**: Web server với bảo mật HTTPS

### 🔧 **ESP32 - Bộ điều khiển servo**
- **MQTT Client**: Kết nối và nhận lệnh từ Pi 5
- **PWM Control**: Điều khiển chính xác góc quay servo
- **Status Monitor**: Gửi thông tin trạng thái về dashboard

### ⚡ **Luồng dữ liệu chi tiết:**

**Khi người dùng kéo slider từ 0° → 90°:**

1. **Browser** → **Node-RED**: `HTTP POST {angle: 90}`
2. **Node-RED** → **Mosquitto**: `MQTT Publish home/servo/cmd {"angle":90}`  
3. **Mosquitto** → **ESP32**: `MQTT Forward message`
4. **ESP32**: 
   - Parse JSON: angle = 90
   - Smooth move servo: 0° → 10° → 20° → ... → 90°
   - Validate: giới hạn 0-180°
5. **ESP32** → **Mosquitto**: `MQTT Publish home/servo/status {"angle":90,"status":"moved"}`
6. **Mosquitto** → **Node-RED**: `MQTT Forward status`
7. **Node-RED** → **Browser**: `WebSocket update gauge display`

**Khi ESP32 bị mất kết nối:**
- Dashboard LED chuyển từ 🟢 → 🔴
- Toast notification hiện "Connection Lost"
- Heartbeat timeout sau 60 giây

**Khi ESP32 khôi phục:**
- Tự động reconnect MQTT
- Gửi status "connected" 
- Dashboard LED trở về 🟢

## Cài đặt và triển khai

### 1. Thiết lập Raspberry Pi 5

```bash
# Chạy script setup tự động
chmod +x setup_pi_services.sh
./setup_pi_services.sh
```

Script này sẽ:
- Cài đặt và cấu hình Mosquitto MQTT Broker
- Cài đặt Node-RED với dashboard
- Cài đặt và cấu hình Nginx với SSL
- Tạo user MQTT với username/password

### 2. Thiết lập Node-RED Dashboard

```bash
# Import flow dashboard
python3 setup_nodered_flow.py
```

### 3. Cấu hình ESP32

1. Cài đặt các thư viện cần thiết trong Arduino IDE:
   - WiFi
   - PubSubClient
   - ESP32Servo
   - ArduinoJson

2. Cập nhật thông tin WiFi và MQTT trong code:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_broker = "10.189.169.194";  // IP của Raspberry Pi
   ```

3. Upload code `esp32_servo_mqtt.ino` lên ESP32

### 4. Kết nối phần cứng

```
ESP32 Pin 18 ───────── Servo SG90 Signal (Vàng)
ESP32 5V ──────────── Servo SG90 VCC (Đỏ)
ESP32 GND ─────────── Servo SG90 GND (Nâu)
```

## Sử dụng hệ thống

### Truy cập Dashboard
- **HTTPS**: `https://[IP_RASPBERRY_PI]`
- **HTTP Node-RED**: `http://[IP_RASPBERRY_PI]:1880/ui`

### Tính năng Dashboard
1. **Thanh trượt góc**: Điều chỉnh góc từ 0-180°
2. **Nút preset**:
   - Home (90°): Vị trí giữa
   - Left (0°): Vị trí trái
   - Right (180°): Vị trí phải
3. **Gauge hiển thị**: Góc hiện tại của servo
4. **LED trạng thái**: Kết nối ESP32
5. **Thông báo lỗi**: Toast notifications

### MQTT Topics
- **Command**: `home/servo/cmd` (Node-RED → ESP32)
  ```json
  {"angle": 90, "timestamp": 1691234567}
  {"preset": "home", "timestamp": 1691234567}
  ```

- **Status**: `home/servo/status` (ESP32 → Node-RED)
  ```json
  {"angle": 90, "status": "moved", "timestamp": 1691234567}
  {"heartbeat": true, "uptime": 12345, "free_heap": 100000}
  ```

### 🔍 **Ví dụ thực tế:**

**Scenario: Di chuyển servo từ 0° sang 135°**

```
[User] Kéo slider → 135°
   ↓
[Browser] POST /servo → Node-RED
   ↓  
[Node-RED] {"angle": 135} → MQTT Publish
   ↓
[MQTT Broker] Forward message → ESP32
   ↓
[ESP32] Nhận: {"angle": 135}
   ↓ Parse JSON
[ESP32] angle = 135, validate OK (0-180)
   ↓ Smooth movement
[Servo] 0° → 15° → 30° → 45° → 60° → 75° → 90° → 105° → 120° → 135°
   ↓ Movement complete
[ESP32] {"angle": 135, "status": "moved"} → MQTT Publish
   ↓
[MQTT Broker] Forward status → Node-RED
   ↓
[Node-RED] Update gauge → WebSocket
   ↓
[Browser] Gauge hiển thị: 135°
```

**Scenario: ESP32 bị ngắt kết nối**
```
[ESP32] WiFi lost → MQTT disconnect
   ↓ (60 giây không có heartbeat)
[Node-RED] Timeout detection → LED status = false
   ↓ 
[Browser] LED indicator: 🟢 → 🔴
[Browser] Toast: "ESP32 connection lost"
```

## Testing và Debug

### Test MQTT Client
```bash
python3 test_mqtt_client.py
```

Tính năng test client:
- Gửi lệnh góc trực tiếp
- Test các preset positions
- Sweep test (quét từ 0-180°)
- Monitor status real-time

### Kiểm tra services
```bash
# Kiểm tra trạng thái services
sudo systemctl status mosquitto
sudo systemctl status nodered
sudo systemctl status nginx

# Xem log
sudo journalctl -u mosquitto -f
sudo journalctl -u nodered -f
```

### Debug MQTT
```bash
# Subscribe topic status
mosquitto_sub -h localhost -u pi -P raspberry -t "home/servo/status"

# Publish test command
mosquitto_pub -h localhost -u pi -P raspberry -t "home/servo/cmd" -m '{"angle":45}'
```

## Bảo mật

1. **HTTPS**: SSL/TLS encryption cho web traffic
2. **MQTT Authentication**: Username/password cho MQTT
3. **Network Isolation**: Chỉ exposed port 80, 443, 1883
4. **Firewall**: Có thể cấu hình UFW để restrict access

## Troubleshooting

### ESP32 không kết nối được MQTT
- Kiểm tra WiFi credentials
- Kiểm tra IP Raspberry Pi
- Kiểm tra username/password MQTT
- Kiểm tra firewall Pi

### Dashboard không hiển thị
- Kiểm tra Node-RED service: `sudo systemctl status nodered`
- Kiểm tra Nginx config: `sudo nginx -t`
- Xem log Node-RED: `sudo journalctl -u nodered -f`

### Servo không chuyển động
- Kiểm tra kết nối phần cứng
- Kiểm tra power supply cho servo
- Kiểm tra ESP32 log qua Serial Monitor

## Mở rộng hệ thống

1. **Multiple Servos**: Thêm nhiều servo với topics khác nhau
2. **Sensor Feedback**: Thêm encoder để feedback vị trí chính xác
3. **Camera Integration**: Thêm camera để monitor servo movement
4. **Mobile App**: Tạo app mobile kết nối MQTT
5. **Voice Control**: Tích hợp voice assistant

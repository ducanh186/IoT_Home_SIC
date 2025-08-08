# IoT Smart Home System

🏠 **Hệ thống nhà thông minh IoT hoàn chỉnh với ESP32 và Raspberry Pi**

## 📋 Tổng quan dự án

Dự án IoT Smart Home System tích hợp đầy đủ các thành phần:
- **4 ESP32 nodes** giám sát môi trường và điều khiển cửa
- **MQTT Broker** trên Raspberry Pi
- **Web Dashboard** theo dõi và điều khiển real-time
- **Node-RED Dashboard** giao diện trực quan
- **SQLite Database** lưu trữ dữ liệu

## 🏗️ Cấu trúc dự án (Đã clean)

```
smart_home_system/
├── bedroom/
│   ├── bedroom_node1_monitor.ino    # ESP32 giám sát phòng ngủ
│   └── bedroom_node2_smart_door.ino # ESP32 điều khiển cửa phòng ngủ
├── livingroom/
│   ├── livingroom_node1_monitor.ino    # ESP32 giám sát phòng khách
│   └── livingroom_node2_smart_door.ino # ESP32 điều khiển cửa phòng khách
└── raspberry_pi/
    ├── mqtt_receiver.py           # Service nhận dữ liệu MQTT
    ├── web_dashboard.py          # Flask web dashboard
    ├── setup_smart_home.sh       # Script cài đặt tự động
    ├── setup_nodered_flow.py     # Cài đặt Node-RED dashboard
    ├── cleanup_old_files.sh      # Dọn dẹp file cũ
    └── templates/
        └── dashboard.html        # Giao diện web
```

## 🔧 Phần cứng

### ESP32 Nodes (x4)
- **DHT11** (GPIO 4): Nhiệt độ, độ ẩm
- **MQ Gas Sensor** (GPIO 34/35): Cảm biến khí gas
- **Flame Sensor** (GPIO 26): Cảm biến lửa
- **LEDs** (GPIO 18, 19, 21): Đèn báo trạng thái
- **Buzzer** (GPIO 5): Chuông báo động
- **Servo Motor** (GPIO 18): Điều khiển cửa
- **IR Sensor** (GPIO 16): Cảm biến hồng ngoại

### Raspberry Pi
- **MQTT Broker**: Mosquitto
- **Web Server**: Flask + SocketIO
- **Database**: SQLite
- **Dashboard**: Node-RED

## 🌐 Cấu hình mạng

- **WiFi**: VIETTEL / 12345678
- **MQTT Broker**: raspberrypi.local:1883 (fallback: 192.168.1.3)
- **Web Dashboard**: http://raspberrypi.local:5000
- **Node-RED**: http://raspberrypi.local:1880
- **MQTT WebSocket**: ws://raspberrypi.local:9001

## 📊 MQTT Topics

```
home/bedroom/node1/temperature
home/bedroom/node1/humidity  
home/bedroom/node1/gas_level
home/bedroom/node1/fire_detected
home/bedroom/node1/gas_status
home/bedroom/node1/fire_status

home/bedroom/node2/door_status
home/bedroom/node2/person_detected
home/bedroom/node2/door_command

home/livingroom/node1/... (tương tự)
home/livingroom/node2/... (tương tự)
```

## 🚀 Hướng dẫn cài đặt

### 1. Chuẩn bị và dọn dẹp

```bash
# Dọn dẹp các file cũ
sudo bash smart_home_system/raspberry_pi/cleanup_old_files.sh
```

### 2. Cài đặt hệ thống Raspberry Pi

```bash
# Cài đặt tự động tất cả services
sudo bash smart_home_system/raspberry_pi/setup_smart_home.sh
```

### 3. Cài đặt Node-RED Dashboard

```bash
# Cài đặt Node-RED flow
python3 smart_home_system/raspberry_pi/setup_nodered_flow.py
```

### 4. Upload code ESP32

1. Mở Arduino IDE
2. Upload các file .ino tương ứng:
   - `bedroom_node1_monitor.ino` → ESP32 #1
   - `bedroom_node2_smart_door.ino` → ESP32 #2  
   - `livingroom_node1_monitor.ino` → ESP32 #3
   - `livingroom_node2_smart_door.ino` → ESP32 #4

## 🖥️ Sử dụng hệ thống

### Web Dashboard
- **URL**: http://raspberrypi.local:5000
- **Tính năng**: 
  - Theo dõi nhiệt độ, độ ẩm real-time
  - Cảnh báo khí gas và lửa
  - Điều khiển cửa từ xa
  - Lịch sử dữ liệu

### Node-RED Dashboard  
- **URL**: http://raspberrypi.local:1880/ui
- **Tính năng**:
  - Biểu đồ gauge trực quan
  - Nút điều khiển cửa
  - Cảnh báo màu sắc
  - Giao diện responsive

## 📈 Tính năng chính

### 🌡️ Giám sát môi trường
- Nhiệt độ, độ ẩm theo thời gian thực
- Cảnh báo mức gas (SAFE/WARNING/DANGER)
- Phát hiện lửa với LED và buzzer báo động

### 🚪 Điều khiển cửa thông minh
- Mở/đóng cửa tự động khi phát hiện người
- Điều khiển từ xa qua web/Node-RED
- Servo motor chuyển động mượt mà
- Feedback trạng thái cửa real-time

### 📊 Lưu trữ và phân tích
- SQLite database lưu tất cả dữ liệu
- API REST để truy xuất dữ liệu
- Real-time updates qua WebSocket
- Export dữ liệu định dạng JSON

## 🔧 Bảo trì và troubleshooting

### Kiểm tra services
```bash
# Kiểm tra MQTT broker
sudo systemctl status mosquitto

# Kiểm tra web dashboard
sudo systemctl status smart-home-web

# Kiểm tra MQTT receiver
sudo systemctl status smart-home-mqtt
```

### Xem logs
```bash
# Logs MQTT receiver
sudo journalctl -u smart-home-mqtt -f

# Logs web dashboard  
sudo journalctl -u smart-home-web -f

# MQTT broker logs
sudo tail -f /var/log/mosquitto/mosquitto.log
```

### Restart services
```bash
# Restart tất cả services
sudo systemctl restart mosquitto
sudo systemctl restart smart-home-mqtt
sudo systemctl restart smart-home-web
```

## 📝 Cấu hình nâng cao

### Thay đổi WiFi credentials
Sửa trong các file .ino:
```cpp
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD"; 
```

### Thay đổi MQTT credentials
Sửa trong `/etc/mosquitto/passwd`:
```bash
sudo mosquitto_passwd /etc/mosquitto/passwd username
```

### Tùy chỉnh web port
Sửa trong `web_dashboard.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

## 🆘 Liên hệ support

- **Project**: IoT Smart Home System
- **Version**: 2.0 Clean Architecture
- **Author**: AI Assistant
- **Last Update**: 2024

---

🎉 **Hệ thống IoT hoàn chỉnh, clean và ready để triển khai!**

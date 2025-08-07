# Smart Door System - Hardware Connections

## 🔌 **ESP32 Wiring Diagram**

```
ESP32 DevKit v1.0
         ## 🔧 **Troubleshooting**

### Servo Not Moving
- Check 5V power supply
- Verify signal wire connection to GPIO 18
- Test with simple servo sweep code
- Check servo arm is not mechanically blocked

### Sensor Not Detecting
- Verify OUT pin connection to GPIO 16
- Check 5V power supply to sensor
- Test with multimeter: OUT should be LOW when detecting
- Ensure sensor has clear line of sight
- Upload test_ir_sensor.ino to verify sensor function

### ⚡ **Quick Sensor Tests:**

**Test với multimeter:**
- OUT pin = LOW (~0V) = Phát hiện người ⭐
- OUT pin = HIGH (~3.3V) = Không có người
- ⚠️ QUAN TRỌNG: Cảm biến này có logic NGƯỢC!

**Test với Serial Monitor:**
- Upload `test_ir_sensor.ino`
- Mở Serial Monitor (115200 baud)
- Kiểm tra: "👤 Person DETECTED! (Sensor = LOW)" hoặc "❌ No person (Sensor = HIGH)"

### Common Sensor Issues

**❌ Sensor luôn báo có người:**
- Nguyên nhân: OUT pin bị ngắn mạch với VCC
- Giải pháp: Kiểm tra kết nối, đảm bảo OUT → GPIO 16

**❌ Sensor không bao giờ báo có người:**
- Nguyên nhân: Thiếu nguồn hoặc OUT pin bị ngắn mạch với GND
- Giải pháp: Kiểm tra 5V power, GND connection, test với multimeter

**❌ Sensor hoạt động không ổn định:**
- Nguyên nhân: Nguồn 5V không ổn định
- Giải pháp: Dùng external power supply, thêm capacitor 100uF gần sensor───────────────────┐
                    │                     │
                    │       ESP32         │
                    │                     │
   Servo Signal ────┤ GPIO 18        3.3V ├──── (Not used)
   Sensor OUT  ────┤ GPIO 16         GND ├──── GND (Servo + Sensor)
                    │ GPIO 17          5V ├──── VCC (Servo + Sensor)
                    │                     │
               GND ─┤ GND                 │
                    │                     │
                    └─────────────────────┘
```

## 🔧 **Servo SG90 Connections**

```
Servo SG90 (3 wires):
├── Signal (Vàng/Cam)  ──► ESP32 GPIO 18
├── VCC (Đỏ)          ──► ESP32 5V
└── GND (Nâu/Đen)     ──► ESP32 GND
```

## 📡 **IR Sensor ARD2-2233 Connections**

```
IR Sensor ARD2-2233 (3 pins):
├── VCC    ──► ESP32 5V
├── GND    ──► ESP32 GND  
└── OUT    ──► ESP32 GPIO 16 (Digital Input)
```

**Sensor Output:**
- **LOW (0V)** = Phát hiện người ⭐
- **HIGH (3.3V)** = Không có người

**⚠️ Lưu ý:** Cảm biến này có logic ngược so với thông thường!

## 🔋 **Power Requirements**

- **ESP32**: 3.3V (via USB hoặc external power)
- **Servo SG90**: 5V, ~500mA max (stall current)
- **IR Sensor**: 5V, ~50mA typical
- **Total**: Recommend 5V/1A power supply minimum

## ⚠️ **Important Notes**

1. **Power Supply**: ESP32's 5V pin có thể cung cấp đủ cho servo nhẹ, nhưng nên dùng external power supply cho ứng dụng thực tế
2. **Signal Level**: GPIO 18 output 3.3V, servo signal pin accept 3.3V-5V
3. **UART**: ESP32 UART1 (pins 16,17) để giao tiếp với sensor
4. **Ground**: Tất cả GND pins phải kết nối chung

## 🛠️ **Assembly Steps**

### Step 1: Prepare Components
- ESP32 DevKit
- Servo SG90 with extension cable
- IR Sensor ARD2-2233
- Breadboard and jumper wires
- Micro USB cable

### Step 2: Connect Servo
1. Connect servo signal wire (yellow/orange) to ESP32 GPIO 18
2. Connect servo VCC (red) to ESP32 5V pin
3. Connect servo GND (brown/black) to ESP32 GND pin

### Step 3: Connect IR Sensor
1. Connect sensor VCC to ESP32 5V pin (shared with servo)
2. Connect sensor GND to ESP32 GND pin (shared with servo)
3. Connect sensor OUT to ESP32 GPIO 16 (digital input pin)

### Step 4: Power Connection
1. Connect ESP32 to Pi via USB cable (for programming and power)
2. Or use external 5V adapter connected to ESP32 VIN pin

### Step 5: Test Connections
1. Power on ESP32
2. Upload test sketch to verify servo movement
3. Check serial monitor for sensor data

## 📐 **Physical Installation**

### Door Mechanism
```
        ┌─────────────┐
        │    Door     │
        │             │
        │      ┌──────┼── Servo arm attachment point
        │      │      │
        │   [Servo]   │
        │      │      │
        │      └──────┼── Servo mounting point
        │             │
        └─────────────┘
```

### Sensor Placement
- **Height**: 1.0-1.5m from floor
- **Range**: 0.5-3.0m detection distance
- **Angle**: Point toward entry path
- **Protection**: Weatherproof housing if outdoor use

## 🔧 **Troubleshooting**

### Servo Not Moving
- Check 5V power supply
- Verify signal wire connection to GPIO 18
- Test with simple servo sweep code
- Check servo arm is not mechanically blocked

### Sensor Not Detecting
- Verify OUT pin connection to GPIO 16
- Check 5V power supply to sensor
- Test with multimeter: OUT should be HIGH when detecting
- Ensure sensor has clear line of sight
- Upload test_ir_sensor.ino to verify sensor function

### Power Issues
- Use multimeter to check 5V rail
- Measure current draw (should be < 1A total)
- Consider external power supply for high-current applications
- Check all GND connections are secure

### Communication Issues
- Verify WiFi credentials in code
- Check MQTT broker IP address
- Test MQTT connection with mosquitto_pub/sub
- Monitor ESP32 serial output for error messages

## 📊 **Expected Performance**

- **Response Time**: < 500ms from detection to door movement
- **Detection Range**: 0.5-3.0m (adjustable in software)
- **Servo Speed**: ~60°/second (adjustable with SMOOTH_DELAY)
- **Power Consumption**: ~200-300mA idle, ~600-800mA during movement
- **WiFi Range**: Typical home WiFi coverage
- **Uptime**: 24/7 operation with proper power supply

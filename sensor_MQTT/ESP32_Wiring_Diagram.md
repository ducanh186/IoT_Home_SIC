# ESP32 NodeMCU Safety Monitoring System - Wiring Diagram

## Pin Configuration Summary

| Component | ESP32 Pin | Description |
|-----------|-----------|-------------|
| **DHT11** | GPIO 4 | Temperature & Humidity sensor |
| **MQ Gas Analog** | GPIO 34 | Gas sensor analog reading (0-4095) |
| **MQ Gas Digital** | GPIO 35 | Gas sensor digital threshold |
| **Flame Sensor** | GPIO 2 | Fire detection sensor |
| **Green LED** | GPIO 18 | Safe status indicator |
| **Yellow LED** | GPIO 19 | Warning status indicator |
| **Red LED** | GPIO 21 | Danger status indicator |
| **Active Buzzer** | GPIO 5 | Audio alarm (3-pin) |

## Detailed Wiring Connections

### 1. DHT11 Temperature & Humidity Sensor
```
DHT11 Pin    →    ESP32 Pin
VCC (Pin 1)  →    3.3V
DATA (Pin 2) →    GPIO 4
NC (Pin 3)   →    Not Connected
GND (Pin 4)  →    GND

Note: Add 10kΩ pull-up resistor between DATA and VCC
```

### 2. MQ Gas Sensor (Dual Output)
```
MQ Sensor Pin     →    ESP32 Pin
VCC              →    5V (or 3.3V depending on model)
GND              →    GND
AO (Analog Out)  →    GPIO 34 (ADC1_CH6)
DO (Digital Out) →    GPIO 35

Analog Range: 0-4095 (12-bit ADC)
Digital: LOW = Gas Detected, HIGH = Normal
```

### 3. Flame Sensor
```
Flame Sensor Pin  →    ESP32 Pin
VCC              →    3.3V
GND              →    GND
DO (Digital Out) →    GPIO 2

Logic: HIGH = No Fire, LOW = Fire Detected
```

### 4. LED Indicator System
```
Green LED (Safe Status):
LED Anode (+)    →    GPIO 18
LED Cathode (-)  →    220Ω Resistor → GND

Yellow LED (Warning Status):
LED Anode (+)    →    GPIO 19
LED Cathode (-)  →    220Ω Resistor → GND

Red LED (Danger Status):
LED Anode (+)    →    GPIO 21
LED Cathode (-)  →    220Ω Resistor → GND

Note: Use 220Ω current limiting resistors for each LED
```

### 5. Active Buzzer (3-Pin)
```
Active Buzzer Pin  →    ESP32 Pin
VCC (Red Wire)    →    3.3V
GND (Black Wire)  →    GND
Signal (Yellow)   →    GPIO 5

Control: HIGH = Beep ON, LOW = Beep OFF
Pattern: 10 beeps for fire/gas alerts
```

### 6. LCD I2C Display (Optional)
```
LCD I2C Pin  →    ESP32 Pin
VCC         →    3.3V
GND         →    GND
SDA         →    GPIO 21 (SDA)
SCL         →    GPIO 22 (SCL)

I2C Address: 0x27 (default)
Size: 16x2 characters
```

## Power Requirements

| Component | Voltage | Current |
|-----------|---------|---------|
| ESP32 NodeMCU | 3.3V | ~250mA |
| DHT11 | 3.3V | 2.5mA |
| MQ Gas Sensor | 5V | 150mA |
| Flame Sensor | 3.3V | 15mA |
| LEDs (3x) | 3.3V | 60mA total |
| Active Buzzer | 3.3V | 30mA |
| LCD I2C | 3.3V | 20mA |

**Total Current Draw: ~530mA**

## Important Notes

1. **ADC Pins**: ESP32 has limited ADC pins. GPIO 34 is ADC1_CH6, ideal for analog sensors.

2. **Pull-up Resistors**: DHT11 requires 10kΩ pull-up resistor on data line.

3. **Current Limiting**: Always use 220Ω resistors with LEDs to prevent damage.

4. **Power Supply**: Use 5V external supply for MQ sensor, 3.3V for others.

5. **Ground Connection**: Ensure all components share common ground with ESP32.

6. **Digital Logic**: 
   - MQ Digital: LOW = Gas detected
   - Flame Sensor: LOW = Fire detected
   - LEDs: HIGH = LED ON
   - Buzzer: HIGH = Beep ON

## Safety Considerations

- Double-check all connections before powering on
- Verify voltage levels match component specifications
- Use breadboard or PCB for secure connections
- Test each component individually before system integration
- Ensure proper ventilation for gas sensor calibration

## MQTT Communication

The system communicates with Raspberry Pi 5 (192.168.1.3) via WiFi:

**Published Topics:**
- `temperature` - DHT11 temperature reading
- `humidity` - DHT11 humidity reading  
- `gas_analog` - MQ analog value (0-4095)
- `gas_digital` - MQ digital state (TRIGGERED/NORMAL)
- `gas_status` - Gas level (SAFE/WARNING/DANGER)
- `fire_detected` - Fire status (FIRE_DETECTED/NO_FIRE)

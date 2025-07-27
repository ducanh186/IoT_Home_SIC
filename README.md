
# ESP32 Safety Monitoring System

## Overview
This project is an IoT safety monitoring system using ESP32 NodeMCU and Raspberry Pi 5. It provides real-time monitoring and alerts for temperature, humidity, gas levels, and fire detection, with MQTT communication to a central Raspberry Pi server.

## Hardware Components
- **ESP32 NodeMCU**: Sensor node and controller
- **Raspberry Pi 5**: MQTT broker and data receiver
- **Sensors**:
  - DHT11 (Temperature & Humidity)
  - MQ Gas Sensor (Analog & Digital)
  - Flame Sensor (Fire detection)
- **Indicators**:
  - Green, Yellow, Red LEDs (Gas status)
  - PWM Buzzer (Audio alerts)

## Features
- Temperature & humidity monitoring
- 3-level gas detection (SAFE, WARNING, DANGER) with LED indicators
- Fire detection with immediate alert
- PWM-controlled buzzer for fire/gas alerts
- MQTT communication to Raspberry Pi 5
- Auto WiFi reconnection & error handling

## System Logic
- **Gas Levels**:
  - SAFE: Green LED ON
  - WARNING: Yellow LED ON + Buzzer
  - DANGER: Red LED ON + Buzzer
- **Fire Detection**:
  - Fire detected: All LEDs flash + Buzzer alert

## Communication Protocol
- **WiFi**: ESP32 connects to local WiFi
- **MQTT**: Sensor data published to Raspberry Pi MQTT broker
  - Topics: `temperature`, `humidity`, `gas_analog`, `gas_digital`, `gas_status`, `fire_detected`

## How It Works
1. ESP32 reads sensor data (temperature, humidity, gas, fire)
2. Controls LEDs and buzzer based on sensor readings
3. Displays readings on Serial Monitor
4. Publishes sensor data to MQTT topics
5. Raspberry Pi receives and processes MQTT messages

## Getting Started
1. Flash the ESP32 with the provided Arduino code (`node1.ino`)
2. Set up Raspberry Pi 5 with an MQTT broker (e.g., Mosquitto)
3. Connect hardware as described in the code comments
4. Power on ESP32 and Raspberry Pi
5. Monitor data via Serial Monitor and MQTT subscriber

## File Structure
- `sensor_MQTT/node1.ino`: Main ESP32 firmware
- `sensor_MQTT/receive_script.py`: Example MQTT subscriber script for Raspberry Pi
- `sensor_MQTT/ESP32_Wiring_Diagram.md`: Hardware wiring diagram

## Example MQTT Topics
- `temperature`: Current temperature (°C)
- `humidity`: Current humidity (%)
- `gas_analog`: Gas sensor analog value
- `gas_digital`: Gas sensor digital status
- `gas_status`: Gas safety level (SAFE/WARNING/DANGER)
- `fire_detected`: Fire status (DETECTED/NO_FIRE)

## License
MIT
- [ ] Set up Raspberry Pi 5 as central hub with MQTT broker

- [ ] Configure ESP32 nodes with MQTT client


# IoT Home Automation System

## Overview
Smart home IoT system using Raspberry Pi 5 as central controller and multiple ESP32 microcontrollers for distributed sensor management.

## Hardware Components
- **Central Controller**: Raspberry Pi 5
- **Sensor Nodes**: 2-5 ESP32 microcontrollers
- Various sensors and actuators

## Features

### Environmental Monitoring
- Temperature and humidity sensing
- Smoke and fire detection with alarm system
- Air quality monitoring

### Security & Access Control
- Infrared motion detection for automatic door opening
- Remote door control capability
- People counting system
- Stranger detection and alerts
- Security camera integration

### Smart Lighting
- Automatic LED control using light sensors
- Voice-controlled lighting system

### Home Automation
- Automatic plant watering system
- Smart trash bin with fullness detection
- Energy consumption monitoring and management

### User Interface
- Display panel showing real-time parameters
- Google Assistant integration for voice control
- Mobile app control (planned)

## System Architecture

### ESP32 Sensor Distribution
Each ESP32 handles specific sensor groups to distribute processing load:
- **Node 1**: Temperature/humidity, light sensors
- **Node 2**: Motion detection, door control
- **Node 3**: Smoke/fire detection, alarm system
- **Node 4**: Plant monitoring, irrigation
- **Node 5**: Trash monitoring, energy management

## Communication Protocol

### MQTT (Message Queuing Telemetry Transport)
- **Broker**: Running on Raspberry Pi 5
- **Protocol**: MQTT over WiFi
- **Advantages**: 
      - Lightweight and efficient
      - Publish/subscribe model
      - Built-in Quality of Service (QoS)
      - Excellent for IoT applications
- **Topics Structure**:
      - `home/sensors/{node_id}/{sensor_type}`
      - `home/actuators/{node_id}/{device_type}`
      - `home/status/{node_id}`

## Implementation Plan

### Phase 1: Basic Setup
- [ ] Set up Raspberry Pi 5 as central hub with MQTT broker
- [ ] Configure ESP32 nodes with MQTT client
- [ ] Establish WiFi communication and MQTT connections

### Phase 2: Core Features
- [ ] Implement environmental monitoring via MQTT
- [ ] Add security features with MQTT messaging
- [ ] Set up automatic door system with MQTT control

### Phase 3: Advanced Features
- [ ] Integrate Google Assistant
- [ ] Add energy management
- [ ] Implement smart irrigation

### Phase 4: Optimization
- [ ] Optimize MQTT message frequency and payload
- [ ] Add redundancy and error handling
- [ ] Create user-friendly interface

## Technical Considerations
- **Data Protocol**: JSON payloads over MQTT
- **Security**: TLS encryption, MQTT authentication
- **Reliability**: MQTT QoS levels, last will and testament
- **Scalability**: Hierarchical MQTT topics for easy expansion


#!/usr/bin/env python3
"""
MQTT Test Client for ESP32 Servo Control
This script allows testing servo commands and monitoring status
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import threading

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "pi"
MQTT_PASSWORD = "1234"

# MQTT Topics
SERVO_CMD_TOPIC = "home/servo/cmd"
SERVO_STATUS_TOPIC = "home/servo/status"

class ServoMQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✓ Connected to MQTT broker")
            self.connected = True
            # Subscribe to servo status
            client.subscribe(SERVO_STATUS_TOPIC)
            print(f"✓ Subscribed to {SERVO_STATUS_TOPIC}")
        else:
            print(f"✗ Failed to connect to MQTT broker. Return code: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        print("✗ Disconnected from MQTT broker")
        self.connected = False
        
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"\n📨 Status received:")
            print(f"   Topic: {topic}")
            
            if "status" in payload:
                print(f"   Status: {payload['status']}")
                
            if "angle" in payload:
                print(f"   Current Angle: {payload['angle']}°")
                
            if "heartbeat" in payload:
                print(f"   Heartbeat - Uptime: {payload.get('uptime', 0)}ms")
                print(f"   Free Heap: {payload.get('free_heap', 0)} bytes")
                print(f"   WiFi RSSI: {payload.get('wifi_rssi', 0)} dBm")
                
            if "timestamp" in payload:
                timestamp = payload['timestamp']
                print(f"   Timestamp: {timestamp}")
                
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse JSON: {e}")
        except Exception as e:
            print(f"✗ Error processing message: {e}")
            
    def connect(self):
        try:
            print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
                
            return self.connected
            
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
            
    def send_angle_command(self, angle):
        """Send angle command to servo"""
        if not self.connected:
            print("✗ Not connected to MQTT broker")
            return False
            
        try:
            command = {
                "angle": angle,
                "timestamp": int(time.time() * 1000)
            }
            
            self.client.publish(SERVO_CMD_TOPIC, json.dumps(command), qos=1)
            print(f"📤 Sent angle command: {angle}°")
            return True
            
        except Exception as e:
            print(f"✗ Error sending angle command: {e}")
            return False
            
    def send_preset_command(self, preset):
        """Send preset command to servo"""
        if not self.connected:
            print("✗ Not connected to MQTT broker")
            return False
            
        try:
            command = {
                "preset": preset,
                "timestamp": int(time.time() * 1000)
            }
            
            self.client.publish(SERVO_CMD_TOPIC, json.dumps(command), qos=1)
            print(f"📤 Sent preset command: {preset}")
            return True
            
        except Exception as e:
            print(f"✗ Error sending preset command: {e}")
            return False
            
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()

def print_menu():
    print("\n" + "="*50)
    print("ESP32 SERVO MQTT TEST CLIENT")
    print("="*50)
    print("Commands:")
    print("  1. Send angle (0-180)")
    print("  2. Home position (90°)")
    print("  3. Left position (0°)")
    print("  4. Right position (180°)")
    print("  5. Sweep test")
    print("  6. Show status")
    print("  q. Quit")
    print("-"*50)

def sweep_test(client):
    """Perform a sweep test from 0 to 180 and back"""
    print("🔄 Starting sweep test...")
    
    # Sweep from 0 to 180
    for angle in range(0, 181, 10):
        client.send_angle_command(angle)
        time.sleep(0.5)
        
    time.sleep(1)
    
    # Sweep from 180 to 0
    for angle in range(180, -1, -10):
        client.send_angle_command(angle)
        time.sleep(0.5)
        
    # Return to center
    client.send_angle_command(90)
    print("✓ Sweep test completed")

def main():
    print("ESP32 Servo MQTT Test Client")
    print("Connecting to MQTT broker...")
    
    # Create and connect MQTT client
    servo_client = ServoMQTTClient()
    
    if not servo_client.connect():
        print("✗ Failed to connect to MQTT broker")
        sys.exit(1)
        
    try:
        while True:
            print_menu()
            choice = input("Enter command: ").strip().lower()
            
            if choice == '1':
                try:
                    angle = int(input("Enter angle (0-180): "))
                    if 0 <= angle <= 180:
                        servo_client.send_angle_command(angle)
                    else:
                        print("✗ Angle must be between 0 and 180")
                except ValueError:
                    print("✗ Invalid angle. Please enter a number.")
                    
            elif choice == '2':
                servo_client.send_preset_command("home")
                
            elif choice == '3':
                servo_client.send_preset_command("left")
                
            elif choice == '4':
                servo_client.send_preset_command("right")
                
            elif choice == '5':
                sweep_test(servo_client)
                
            elif choice == '6':
                print("📊 Listening for status updates... (Press Enter to continue)")
                input()
                
            elif choice == 'q':
                break
                
            else:
                print("✗ Invalid command")
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        
    finally:
        print("Disconnecting...")
        servo_client.disconnect()
        print("Goodbye!")

if __name__ == "__main__":
    main()

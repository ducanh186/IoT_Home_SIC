#!/usr/bin/env python3
"""
Smart Door System - MQTT Test Client
Test MQTT connectivity và simulate door commands
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime

# MQTT Configuration
MQTT_HOST = "10.189.169.194"
MQTT_PORT = 1883
MQTT_USER = "pi"
MQTT_PASS = "1234"

# Topics
TOPIC_CMD = "door/cmd"
TOPIC_STATUS = "door/status"
TOPIC_SENSOR = "door/sensor"

class SmartDoorTestClient:
    def __init__(self):
        self.client = mqtt.Client(client_id="SmartDoorTest")
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            self.connected = True
            
            # Subscribe to all door topics
            client.subscribe(f"{TOPIC_STATUS}")
            client.subscribe(f"{TOPIC_SENSOR}")
            print(f"📡 Subscribed to topics: {TOPIC_STATUS}, {TOPIC_SENSOR}")
            
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
            self.connected = False
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n📨 [{timestamp}] {topic}:")
            print(f"   {json.dumps(payload, indent=2)}")
            
        except json.JSONDecodeError:
            print(f"📨 {topic}: {msg.payload.decode()}")
    
    def on_disconnect(self, client, userdata, rc):
        print("❌ Disconnected from MQTT broker")
        self.connected = False
    
    def connect(self):
        try:
            print(f"🔗 Connecting to MQTT broker {MQTT_HOST}:{MQTT_PORT}...")
            self.client.connect(MQTT_HOST, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
                
            return self.connected
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
    
    def send_command(self, command):
        if not self.connected:
            print("❌ Not connected to MQTT broker")
            return False
        
        try:
            command["timestamp"] = int(time.time())
            payload = json.dumps(command)
            
            result = self.client.publish(TOPIC_CMD, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Command sent: {payload}")
                return True
            else:
                print(f"❌ Failed to send command: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False

def print_menu():
    print("\n" + "="*50)
    print("🚪 Smart Door System - Test Client")
    print("="*50)
    print("1. Open door")
    print("2. Close door") 
    print("3. Set angle (0-90)")
    print("4. Test auto commands")
    print("5. Monitor only (no commands)")
    print("6. Connection test")
    print("0. Exit")
    print("-"*50)

def test_auto_commands(client):
    """Test tự động các lệnh"""
    print("\n🤖 Starting automated test sequence...")
    
    commands = [
        {"action": "open", "source": "test"},
        {"angle": 45, "source": "test"},
        {"angle": 90, "source": "test"},
        {"action": "close", "source": "test"},
        {"angle": 30, "source": "test"},
        {"angle": 0, "source": "test"}
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n📤 Test {i}/6: {cmd}")
        client.send_command(cmd)
        time.sleep(3)  # Wait 3 seconds between commands
    
    print("\n✅ Automated test completed!")

def connection_test():
    """Test kết nối MQTT"""
    print("\n🔍 Testing MQTT connection...")
    
    test_client = mqtt.Client(client_id="ConnectionTest")
    test_client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    try:
        test_client.connect(MQTT_HOST, MQTT_PORT, 60)
        print("✅ MQTT connection successful!")
        test_client.disconnect()
        return True
    except Exception as e:
        print(f"❌ MQTT connection failed: {e}")
        return False

def main():
    print("🚪 Smart Door System - MQTT Test Client")
    print("======================================")
    
    # Create client
    client = SmartDoorTestClient()
    
    try:
        while True:
            print_menu()
            choice = input("Enter your choice: ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
                
            elif choice == "1":
                if not client.connected:
                    if not client.connect():
                        continue
                client.send_command({"action": "open", "source": "manual"})
                
            elif choice == "2":
                if not client.connected:
                    if not client.connect():
                        continue
                client.send_command({"action": "close", "source": "manual"})
                
            elif choice == "3":
                angle = input("Enter angle (0-90): ").strip()
                try:
                    angle_val = int(angle)
                    if 0 <= angle_val <= 90:
                        if not client.connected:
                            if not client.connect():
                                continue
                        client.send_command({"angle": angle_val, "source": "manual"})
                    else:
                        print("❌ Angle must be between 0 and 90")
                except ValueError:
                    print("❌ Invalid angle value")
                    
            elif choice == "4":
                if not client.connected:
                    if not client.connect():
                        continue
                test_auto_commands(client)
                
            elif choice == "5":
                if not client.connected:
                    if not client.connect():
                        continue
                print("👁️  Monitoring mode - Press Ctrl+C to stop")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n⏹️  Monitoring stopped")
                    
            elif choice == "6":
                connection_test()
                
            else:
                print("❌ Invalid choice")
                
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        
    finally:
        if client.connected:
            client.disconnect()
        print("🔚 Test client terminated")

if __name__ == "__main__":
    main()

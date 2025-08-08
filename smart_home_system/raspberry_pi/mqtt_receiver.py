#!/usr/bin/env python3
"""
IoT Home MQTT Data Receiver & Logger
Nhận dữ liệu từ tất cả các ESP32 nodes và log vào database
"""

import paho.mqtt.client as mqtt
import json
import sqlite3
import logging
from datetime import datetime
import os

# ===== MQTT CONFIGURATION =====
MQTT_BROKER = "localhost"  # Chạy trên chính Raspberry Pi
MQTT_PORT = 1883
MQTT_USERNAME = "pi101"
MQTT_PASSWORD = "1234"

# ===== DATABASE CONFIGURATION =====
DB_FILE = "/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/smart_home.db"

# ===== LOGGING CONFIGURATION =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/mqtt_receiver.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartHomeMQTTReceiver:
    def __init__(self):
        self.client = mqtt.Client()
        # self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)  # Tạm thời tắt auth
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with tables for sensor data"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Environmental data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environmental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                node TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                gas_analog INTEGER,
                gas_status TEXT,
                fire_detected BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Door status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS door_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                node TEXT NOT NULL,
                door_state TEXT,
                door_angle INTEGER,
                presence_detected BOOLEAN,
                last_action TEXT,
                manual_override BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # System status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT,
                node TEXT,
                device_type TEXT,
                status TEXT,
                ip_address TEXT,
                uptime INTEGER,
                free_heap INTEGER,
                wifi_rssi INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                node TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT,
                severity TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to all topics
            topics = [
                "home/+/+/+/+",  # All sensor data
                "home/system/+", # System status
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to: {topic}")
                
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT broker")
        
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received [{topic}]: {payload}")
            
            # Parse topic
            topic_parts = topic.split('/')
            
            if len(topic_parts) >= 5 and topic_parts[0] == "home":
                room = topic_parts[1]
                node = topic_parts[2]
                device = topic_parts[3]
                attribute = topic_parts[4]
                
                self.process_sensor_data(room, node, device, attribute, payload)
                
            elif topic.startswith("home/system/"):
                self.process_system_data(topic, payload)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def process_sensor_data(self, room, node, device, attribute, payload):
        """Process sensor data and store in database"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            if device == "temperature_sensor" and attribute == "value":
                # Store temperature data
                cursor.execute('''
                    INSERT OR REPLACE INTO environmental_data 
                    (room, node, temperature, timestamp) 
                    VALUES (?, ?, ?, ?)
                ''', (room, node, float(payload), datetime.now()))
                
            elif device == "humidity_sensor" and attribute == "value":
                # Store humidity data
                cursor.execute('''
                    UPDATE environmental_data 
                    SET humidity = ?, timestamp = ?
                    WHERE room = ? AND node = ? AND date(timestamp) = date('now')
                ''', (float(payload), datetime.now(), room, node))
                
            elif device == "gas_sensor":
                if attribute == "analog_value":
                    cursor.execute('''
                        UPDATE environmental_data 
                        SET gas_analog = ?, timestamp = ?
                        WHERE room = ? AND node = ? AND date(timestamp) = date('now')
                    ''', (int(payload), datetime.now(), room, node))
                elif attribute == "status":
                    cursor.execute('''
                        UPDATE environmental_data 
                        SET gas_status = ?, timestamp = ?
                        WHERE room = ? AND node = ? AND date(timestamp) = date('now')
                    ''', (payload, datetime.now(), room, node))
                    
                    # Check for gas alerts
                    if payload in ["WARNING", "DANGER"]:
                        self.create_alert(room, node, "GAS_ALERT", f"Gas level: {payload}", 
                                        "HIGH" if payload == "DANGER" else "MEDIUM")
                        
            elif device == "flame_sensor" and attribute == "alert":
                cursor.execute('''
                    UPDATE environmental_data 
                    SET fire_detected = ?, timestamp = ?
                    WHERE room = ? AND node = ? AND date(timestamp) = date('now')
                ''', (payload == "FIRE_DETECTED", datetime.now(), room, node))
                
                # Fire alert
                if payload == "FIRE_DETECTED":
                    self.create_alert(room, node, "FIRE_ALERT", "Fire detected!", "CRITICAL")
                    
            elif device == "door" and attribute == "status":
                # Parse door status JSON
                door_data = json.loads(payload)
                cursor.execute('''
                    INSERT INTO door_status 
                    (room, node, door_state, door_angle, presence_detected, last_action, manual_override, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (room, node, door_data.get('state'), door_data.get('angle'),
                      door_data.get('presence'), door_data.get('last_action'),
                      door_data.get('manual_override'), datetime.now()))
                      
            conn.commit()
            
        except Exception as e:
            logger.error(f"Database error: {e}")
        finally:
            conn.close()
            
    def process_system_data(self, topic, payload):
        """Process system status data"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            data = json.loads(payload)
            
            if topic == "home/system/heartbeat":
                cursor.execute('''
                    INSERT INTO system_status 
                    (room, node, device_type, status, uptime, free_heap, wifi_rssi, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data.get('room'), data.get('node'), data.get('type'), 'online',
                      data.get('uptime'), data.get('free_heap'), data.get('wifi_rssi'), 
                      datetime.now()))
                      
            elif topic == "home/system/status":
                cursor.execute('''
                    INSERT INTO system_status 
                    (room, node, status, ip_address, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data.get('room'), data.get('node'), data.get('status'),
                      data.get('ip'), datetime.now()))
                      
            conn.commit()
            
        except Exception as e:
            logger.error(f"System data processing error: {e}")
        finally:
            conn.close()
            
    def create_alert(self, room, node, alert_type, message, severity):
        """Create alert in database"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO alerts (room, node, alert_type, message, severity, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (room, node, alert_type, message, severity, datetime.now()))
            
            conn.commit()
            logger.warning(f"ALERT: {room}/{node} - {alert_type}: {message}")
            
        except Exception as e:
            logger.error(f"Alert creation error: {e}")
        finally:
            conn.close()
            
    def run(self):
        """Start the MQTT receiver"""
        try:
            logger.info("Starting Smart Home MQTT Receiver...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("Shutting down MQTT receiver...")
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error running MQTT receiver: {e}")

if __name__ == "__main__":
    receiver = SmartHomeMQTTReceiver()
    receiver.run()

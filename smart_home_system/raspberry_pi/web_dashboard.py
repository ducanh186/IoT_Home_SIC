#!/usr/bin/env python3
"""
Smart Home Web Dashboard
Dashboard web để quản lý và điều khiển toàn bộ hệ thống IoT Home
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import sqlite3
import json
import threading
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_home_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "pi101"
MQTT_PASSWORD = "1234"
DB_FILE = "/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/smart_home.db"

# Global variables for real-time data
current_data = {
    'bedroom': {
        'node1': {'temperature': 0, 'humidity': 0, 'gas_status': 'SAFE', 'fire': False},
        'node2': {'door_state': 'closed', 'presence': False}
    },
    'livingroom': {
        'node1': {'temperature': 0, 'humidity': 0, 'gas_status': 'SAFE', 'fire': False},
        'node2': {'door_state': 'closed', 'presence': False}
    }
}

# MQTT Client setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        # Subscribe to all topics
        client.subscribe("home/+/+/+/+")
        client.subscribe("home/system/+")
    else:
        print(f"Failed to connect to MQTT broker: {rc}")

def on_mqtt_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        topic_parts = topic.split('/')
        
        if len(topic_parts) >= 5:
            room = topic_parts[1]
            node = topic_parts[2]
            device = topic_parts[3]
            attribute = topic_parts[4]
            
            # Update current data
            if room in current_data and node in current_data[room]:
                if device == "temperature_sensor" and attribute == "value":
                    current_data[room][node]['temperature'] = float(payload)
                elif device == "humidity_sensor" and attribute == "value":
                    current_data[room][node]['humidity'] = float(payload)
                elif device == "gas_sensor" and attribute == "status":
                    current_data[room][node]['gas_status'] = payload
                elif device == "flame_sensor" and attribute == "alert":
                    current_data[room][node]['fire'] = (payload == "FIRE_DETECTED")
                elif device == "door" and attribute == "status":
                    door_data = json.loads(payload)
                    current_data[room][node]['door_state'] = door_data.get('state', 'unknown')
                    current_data[room][node]['presence'] = door_data.get('presence', False)
            
            # Emit real-time data to connected clients
            socketio.emit('sensor_update', {
                'room': room,
                'node': node,
                'device': device,
                'attribute': attribute,
                'value': payload,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# Database functions
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_recent_data(room=None, hours=24):
    """Get recent sensor data from database"""
    conn = get_db_connection()
    
    query = '''
        SELECT * FROM environmental_data 
        WHERE timestamp > datetime('now', '-{} hours')
    '''.format(hours)
    
    if room:
        query += f" AND room = '{room}'"
        
    query += " ORDER BY timestamp DESC LIMIT 100"
    
    data = conn.execute(query).fetchall()
    conn.close()
    
    return [dict(row) for row in data]

def get_alerts(resolved=False):
    """Get alerts from database"""
    conn = get_db_connection()
    
    query = '''
        SELECT * FROM alerts 
        WHERE resolved = ?
        ORDER BY timestamp DESC LIMIT 50
    '''
    
    alerts = conn.execute(query, (resolved,)).fetchall()
    conn.close()
    
    return [dict(row) for row in alerts]

# Routes
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/current_data')
def api_current_data():
    return jsonify(current_data)

@app.route('/api/recent_data/<room>')
def api_recent_data(room):
    data = get_recent_data(room, hours=24)
    return jsonify(data)

@app.route('/api/alerts')
def api_alerts():
    alerts = get_alerts(resolved=False)
    return jsonify(alerts)

@app.route('/api/control_door', methods=['POST'])
def api_control_door():
    try:
        data = request.get_json()
        room = data.get('room')
        action = data.get('action')  # 'open', 'close', 'toggle'
        
        if not room or not action:
            return jsonify({'error': 'Missing room or action'}), 400
        
        # Publish MQTT command
        topic = f"home/{room}/node2/door/command"
        command = {
            'action': action,
            'source': 'web',
            'timestamp': datetime.now().isoformat()
        }
        
        mqtt_client.publish(topic, json.dumps(command))
        
        return jsonify({'success': True, 'message': f'Door {action} command sent to {room}'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_stats')
def api_system_stats():
    """Get system statistics"""
    conn = get_db_connection()
    
    # Count alerts by severity
    alert_stats = conn.execute('''
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        WHERE resolved = 0 
        GROUP BY severity
    ''').fetchall()
    
    # Count online devices
    online_devices = conn.execute('''
        SELECT COUNT(*) as count 
        FROM system_status 
        WHERE timestamp > datetime('now', '-5 minutes') 
        AND status = 'online'
    ''').fetchone()
    
    # Recent environmental readings
    recent_readings = conn.execute('''
        SELECT COUNT(*) as count 
        FROM environmental_data 
        WHERE timestamp > datetime('now', '-1 hour')
    ''').fetchone()
    
    conn.close()
    
    return jsonify({
        'alerts': [dict(row) for row in alert_stats],
        'online_devices': dict(online_devices)['count'],
        'recent_readings': dict(recent_readings)['count']
    })

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('current_data', current_data)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_door_control')
def handle_door_control(data):
    room = data.get('room')
    action = data.get('action')
    
    if room and action:
        topic = f"home/{room}/node2/door/command"
        command = {
            'action': action,
            'source': 'web',
            'timestamp': datetime.now().isoformat()
        }
        
        mqtt_client.publish(topic, json.dumps(command))
        emit('door_command_sent', {'room': room, 'action': action})

def start_mqtt_client():
    """Start MQTT client in background thread"""
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT client error: {e}")

if __name__ == '__main__':
    # Ensure database exists
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    # Start MQTT client in background thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    print("🌐 Starting Smart Home Dashboard...")
    print("📊 Dashboard will be available at: http://raspberrypi.local:5000")
    
    # Start Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

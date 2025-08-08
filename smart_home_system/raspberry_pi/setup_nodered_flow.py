#!/usr/bin/env python3
"""
Node-RED Flow Setup Script
Tạo và cài đặt Node-RED flow cho Smart Home dashboard
"""

import json
import requests
import time
import subprocess

# Node-RED flow configuration
NODERED_FLOW = [
    {
        "id": "smart_home_tab",
        "type": "tab",
        "label": "🏠 Smart Home Dashboard",
        "disabled": False,
        "info": ""
    },
    
    # MQTT Input Nodes
    {
        "id": "mqtt_bedroom_temp",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Bedroom Temperature",
        "topic": "home/bedroom/node1/temperature_sensor/value",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 100,
        "wires": [["temp_gauge_bedroom"]]
    },
    
    {
        "id": "mqtt_bedroom_humidity",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Bedroom Humidity",
        "topic": "home/bedroom/node1/humidity_sensor/value",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 160,
        "wires": [["humidity_gauge_bedroom"]]
    },
    
    {
        "id": "mqtt_bedroom_gas",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Bedroom Gas",
        "topic": "home/bedroom/node1/gas_sensor/status",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 220,
        "wires": [["gas_status_bedroom"]]
    },
    
    {
        "id": "mqtt_bedroom_door",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Bedroom Door",
        "topic": "home/bedroom/node2/door/status",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 280,
        "wires": [["door_status_bedroom"]]
    },
    
    # Living Room MQTT Inputs
    {
        "id": "mqtt_living_temp",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Living Room Temperature",
        "topic": "home/livingroom/node1/temperature_sensor/value",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 400,
        "wires": [["temp_gauge_living"]]
    },
    
    {
        "id": "mqtt_living_humidity",
        "type": "mqtt in",
        "z": "smart_home_tab",
        "name": "Living Room Humidity",
        "topic": "home/livingroom/node1/humidity_sensor/value",
        "qos": "0",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 180,
        "y": 460,
        "wires": [["humidity_gauge_living"]]
    },
    
    # Dashboard UI Nodes - Bedroom
    {
        "id": "temp_gauge_bedroom",
        "type": "ui_gauge",
        "z": "smart_home_tab",
        "name": "🌡️ Bedroom Temperature",
        "group": "bedroom_group",
        "order": 1,
        "width": 6,
        "height": 4,
        "gtype": "gage",
        "title": "Temperature (°C)",
        "label": "°C",
        "format": "{{value}}",
        "min": 0,
        "max": 50,
        "colors": ["#0066cc", "#00cc00", "#cc0000"],
        "seg1": 20,
        "seg2": 30,
        "className": "",
        "x": 460,
        "y": 100,
        "wires": []
    },
    
    {
        "id": "humidity_gauge_bedroom",
        "type": "ui_gauge",
        "z": "smart_home_tab",
        "name": "💧 Bedroom Humidity",
        "group": "bedroom_group",
        "order": 2,
        "width": 6,
        "height": 4,
        "gtype": "gage",
        "title": "Humidity (%)",
        "label": "%",
        "format": "{{value}}",
        "min": 0,
        "max": 100,
        "colors": ["#cc0000", "#00cc00", "#0066cc"],
        "seg1": 30,
        "seg2": 70,
        "className": "",
        "x": 460,
        "y": 160,
        "wires": []
    },
    
    {
        "id": "gas_status_bedroom",
        "type": "ui_text",
        "z": "smart_home_tab",
        "group": "bedroom_group",
        "order": 3,
        "width": 6,
        "height": 2,
        "name": "💨 Gas Status",
        "label": "Gas Level:",
        "format": "{{msg.payload}}",
        "layout": "row-spread",
        "className": "",
        "x": 460,
        "y": 220,
        "wires": []
    },
    
    {
        "id": "door_status_bedroom",
        "type": "ui_text",
        "z": "smart_home_tab",
        "group": "bedroom_door_group",
        "order": 1,
        "width": 6,
        "height": 2,
        "name": "🚪 Door Status",
        "label": "Door:",
        "format": "{{msg.payload}}",
        "layout": "row-spread",
        "className": "",
        "x": 460,
        "y": 280,
        "wires": []
    },
    
    # Dashboard UI Nodes - Living Room
    {
        "id": "temp_gauge_living",
        "type": "ui_gauge",
        "z": "smart_home_tab",
        "name": "🌡️ Living Room Temperature",
        "group": "living_group",
        "order": 1,
        "width": 6,
        "height": 4,
        "gtype": "gage",
        "title": "Temperature (°C)",
        "label": "°C",
        "format": "{{value}}",
        "min": 0,
        "max": 50,
        "colors": ["#0066cc", "#00cc00", "#cc0000"],
        "seg1": 20,
        "seg2": 30,
        "className": "",
        "x": 480,
        "y": 400,
        "wires": []
    },
    
    {
        "id": "humidity_gauge_living",
        "type": "ui_gauge",
        "z": "smart_home_tab",
        "name": "💧 Living Room Humidity",
        "group": "living_group",
        "order": 2,
        "width": 6,
        "height": 4,
        "gtype": "gage",
        "title": "Humidity (%)",
        "label": "%",
        "format": "{{value}}",
        "min": 0,
        "max": 100,
        "colors": ["#cc0000", "#00cc00", "#0066cc"],
        "seg1": 30,
        "seg2": 70,
        "className": "",
        "x": 480,
        "y": 460,
        "wires": []
    },
    
    # Door Control Buttons
    {
        "id": "bedroom_door_open",
        "type": "ui_button",
        "z": "smart_home_tab",
        "name": "Open Bedroom Door",
        "group": "bedroom_door_group",
        "order": 2,
        "width": 3,
        "height": 1,
        "passthru": False,
        "label": "Open",
        "tooltip": "Open bedroom door",
        "color": "",
        "bgcolor": "#28a745",
        "className": "",
        "icon": "",
        "payload": '{"action":"open","source":"nodered"}',
        "payloadType": "str",
        "topic": "",
        "topicType": "str",
        "x": 200,
        "y": 340,
        "wires": [["mqtt_bedroom_door_cmd"]]
    },
    
    {
        "id": "bedroom_door_close",
        "type": "ui_button",
        "z": "smart_home_tab",
        "name": "Close Bedroom Door",
        "group": "bedroom_door_group",
        "order": 3,
        "width": 3,
        "height": 1,
        "passthru": False,
        "label": "Close",
        "tooltip": "Close bedroom door",
        "color": "",
        "bgcolor": "#dc3545",
        "className": "",
        "icon": "",
        "payload": '{"action":"close","source":"nodered"}',
        "payloadType": "str",
        "topic": "",
        "topicType": "str",
        "x": 200,
        "y": 380,
        "wires": [["mqtt_bedroom_door_cmd"]]
    },
    
    # MQTT Output for door commands
    {
        "id": "mqtt_bedroom_door_cmd",
        "type": "mqtt out",
        "z": "smart_home_tab",
        "name": "Bedroom Door Command",
        "topic": "home/bedroom/node2/door/command",
        "qos": "0",
        "retain": False,
        "respTopic": "",
        "contentType": "",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": "mqtt_broker",
        "x": 500,
        "y": 360,
        "wires": []
    },
    
    # MQTT Broker Configuration
    {
        "id": "mqtt_broker",
        "type": "mqtt-broker",
        "name": "Smart Home MQTT",
        "broker": "localhost",
        "port": "1883",
        "clientid": "nodered_client",
        "autoConnect": True,
        "usetls": False,
        "protocolVersion": "4",
        "keepalive": "60",
        "cleansession": True,
        "autoUnsubscribe": True,
        "birthTopic": "",
        "birthQos": "0",
        "birthRetain": False,
        "birthPayload": "",
        "birthMsg": {},
        "closeTopic": "",
        "closeQos": "0",
        "closeRetain": False,
        "closePayload": "",
        "closeMsg": {},
        "willTopic": "",
        "willQos": "0",
        "willRetain": False,
        "willPayload": "",
        "willMsg": {},
        "userProps": "",
        "sessionExpiry": "",
        "credentials": {
            "user": "pi101",
            "password": "1234"
        }
    },
    
    # UI Groups
    {
        "id": "bedroom_group",
        "type": "ui_group",
        "name": "🛏️ Bedroom Sensors",
        "tab": "smart_home_ui",
        "order": 1,
        "disp": True,
        "width": "12",
        "collapse": False,
        "className": ""
    },
    
    {
        "id": "bedroom_door_group",
        "type": "ui_group",
        "name": "🚪 Bedroom Door",
        "tab": "smart_home_ui",
        "order": 2,
        "disp": True,
        "width": "12",
        "collapse": False,
        "className": ""
    },
    
    {
        "id": "living_group",
        "type": "ui_group",
        "name": "🛋️ Living Room Sensors",
        "tab": "smart_home_ui",
        "order": 3,
        "disp": True,
        "width": "12",
        "collapse": False,
        "className": ""
    },
    
    # UI Tab
    {
        "id": "smart_home_ui",
        "type": "ui_tab",
        "name": "🏠 Smart Home",
        "icon": "dashboard",
        "disabled": False,
        "hidden": False
    }
]

def setup_nodered_flow():
    """Setup Node-RED flow for Smart Home dashboard"""
    print("🎛️ Setting up Node-RED flow...")
    
    try:
        # Wait for Node-RED to start
        print("⏳ Waiting for Node-RED to start...")
        time.sleep(10)
        
        # Deploy the flow
        response = requests.post(
            'http://localhost:1880/flows',
            json=NODERED_FLOW,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Node-RED flow deployed successfully!")
            print("🌐 Access Node-RED dashboard at: http://raspberrypi.local:1880/ui")
        else:
            print(f"❌ Failed to deploy Node-RED flow: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error setting up Node-RED flow: {e}")
        print("💡 You can manually import the flow later")

def install_nodered_nodes():
    """Install required Node-RED nodes"""
    print("📦 Installing Node-RED dashboard nodes...")
    
    nodes_to_install = [
        "node-red-dashboard",
        "node-red-contrib-ui-led"
    ]
    
    for node in nodes_to_install:
        try:
            result = subprocess.run(
                ['npm', 'install', '--prefix', '/home/pi/.node-red', node],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Installed {node}")
            else:
                print(f"❌ Failed to install {node}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error installing {node}: {e}")

def save_flow_json():
    """Save flow as JSON file for manual import"""
    flow_file = "/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/nodered_flow.json"
    
    try:
        with open(flow_file, 'w') as f:
            json.dump(NODERED_FLOW, f, indent=2)
        print(f"💾 Node-RED flow saved to: {flow_file}")
        print("📝 You can import this flow manually in Node-RED if auto-deployment fails")
        
    except Exception as e:
        print(f"❌ Error saving flow file: {e}")

if __name__ == "__main__":
    print("🎛️ Node-RED Flow Setup for Smart Home")
    print("=====================================")
    
    # Install required nodes
    install_nodered_nodes()
    
    # Save flow JSON for manual import
    save_flow_json()
    
    # Try to deploy the flow automatically
    setup_nodered_flow()
    
    print("\n🎉 Node-RED setup complete!")
    print("📊 Access your dashboard at: http://raspberrypi.local:1880/ui")
    print("🔧 Node-RED editor: http://raspberrypi.local:1880")

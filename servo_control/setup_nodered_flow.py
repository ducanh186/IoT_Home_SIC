#!/usr/bin/env python3
"""
Node-RED Flow Setup for ESP32 Servo Control
This script creates and imports the Node-RED flow for servo control dashboard
"""

import json
import requests
import time
import sys

# Node-RED settings
NODERED_URL = "http://localhost:1880"
FLOW_NAME = "ESP32 Servo Control"

# Node-RED flow configuration
SERVO_FLOW = [
    {
        "id": "servo_control_tab",
        "type": "tab",
        "label": "ESP32 Servo Control",
        "disabled": False,
        "info": "Dashboard for controlling ESP32 servo motor via MQTT"
    },
    {
        "id": "mqtt_broker",
        "type": "mqtt-broker",
        "name": "Local Mosquitto",
        "broker": "localhost",
        "port": "1883",
        "clientid": "nodered_servo",
        "usetls": False,
        "compatmode": False,
        "keepalive": "60",
        "cleansession": True,
        "birthTopic": "",
        "birthQos": "0",
        "birthPayload": "",
        "closeTopic": "",
        "closeQos": "0",
        "closePayload": "",
        "willTopic": "",
        "willQos": "0",
        "willPayload": "",
        "credentials": {
            "user": "pi",
            "password": "1234"
        }
    },
    {
        "id": "ui_group_servo",
        "type": "ui_group",
        "name": "Servo Control",
        "tab": "ui_tab_servo",
        "order": 1,
        "disp": True,
        "width": "6",
        "collapse": False
    },
    {
        "id": "ui_tab_servo",
        "type": "ui_tab",
        "name": "Servo Dashboard",
        "icon": "dashboard",
        "order": 1,
        "disabled": False,
        "hidden": False
    },
    {
        "id": "ui_group_status",
        "type": "ui_group",
        "name": "System Status",
        "tab": "ui_tab_servo",
        "order": 2,
        "disp": True,
        "width": "6",
        "collapse": False
    },
    {
        "id": "slider_angle",
        "type": "ui_slider",
        "z": "servo_control_tab",
        "name": "Servo Angle",
        "label": "Angle (degrees)",
        "tooltip": "Set servo angle from 0 to 180 degrees",
        "group": "ui_group_servo",
        "order": 1,
        "width": 0,
        "height": 0,
        "passthru": True,
        "outs": "end",
        "topic": "angle",
        "min": 0,
        "max": 180,
        "step": 1,
        "x": 130,
        "y": 100,
        "wires": [["format_servo_cmd"]]
    },
    {
        "id": "btn_home",
        "type": "ui_button",
        "z": "servo_control_tab",
        "name": "Home Position",
        "group": "ui_group_servo",
        "order": 2,
        "width": 0,
        "height": 0,
        "passthru": False,
        "label": "Home (90°)",
        "tooltip": "Move servo to home position (90 degrees)",
        "color": "",
        "bgcolor": "#2196F3",
        "icon": "home",
        "payload": '{"preset":"home"}',
        "payloadType": "json",
        "topic": "",
        "x": 130,
        "y": 160,
        "wires": [["mqtt_servo_cmd"]]
    },
    {
        "id": "btn_left",
        "type": "ui_button",
        "z": "servo_control_tab",
        "name": "Left Position",
        "group": "ui_group_servo",
        "order": 3,
        "width": 0,
        "height": 0,
        "passthru": False,
        "label": "Left (0°)",
        "tooltip": "Move servo to left position (0 degrees)",
        "color": "",
        "bgcolor": "#FF9800",
        "icon": "keyboard_arrow_left",
        "payload": '{"preset":"left"}',
        "payloadType": "json",
        "topic": "",
        "x": 130,
        "y": 220,
        "wires": [["mqtt_servo_cmd"]]
    },
    {
        "id": "btn_right",
        "type": "ui_button",
        "z": "servo_control_tab",
        "name": "Right Position",
        "group": "ui_group_servo",
        "order": 4,
        "width": 0,
        "height": 0,
        "passthru": False,
        "label": "Right (180°)",
        "tooltip": "Move servo to right position (180 degrees)",
        "color": "",
        "bgcolor": "#FF9800",
        "icon": "keyboard_arrow_right",
        "payload": '{"preset":"right"}',
        "payloadType": "json",
        "topic": "",
        "x": 130,
        "y": 280,
        "wires": [["mqtt_servo_cmd"]]
    },
    {
        "id": "format_servo_cmd",
        "type": "function",
        "z": "servo_control_tab",
        "name": "Format Servo Command",
        "func": "msg.payload = {\n    \"angle\": msg.payload,\n    \"timestamp\": Date.now()\n};\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "x": 350,
        "y": 100,
        "wires": [["mqtt_servo_cmd"]]
    },
    {
        "id": "mqtt_servo_cmd",
        "type": "mqtt out",
        "z": "servo_control_tab",
        "name": "Servo Command",
        "topic": "home/servo/cmd",
        "qos": "1",
        "retain": "false",
        "broker": "mqtt_broker",
        "x": 580,
        "y": 180,
        "wires": []
    },
    {
        "id": "mqtt_servo_status",
        "type": "mqtt in",
        "z": "servo_control_tab",
        "name": "Servo Status",
        "topic": "home/servo/status",
        "qos": "1",
        "datatype": "auto",
        "broker": "mqtt_broker",
        "x": 130,
        "y": 400,
        "wires": [["parse_status"]]
    },
    {
        "id": "parse_status",
        "type": "json",
        "z": "servo_control_tab",
        "name": "Parse JSON",
        "property": "payload",
        "action": "",
        "pretty": False,
        "x": 310,
        "y": 400,
        "wires": [["route_status"]]
    },
    {
        "id": "route_status",
        "type": "switch",
        "z": "servo_control_tab",
        "name": "Route Status",
        "property": "payload.status",
        "propertyType": "msg",
        "rules": [
            {
                "t": "eq",
                "v": "moved",
                "vt": "str"
            },
            {
                "t": "eq",
                "v": "connected",
                "vt": "str"
            },
            {
                "t": "cont",
                "v": "error",
                "vt": "str"
            },
            {
                "t": "else"
            }
        ],
        "checkall": "true",
        "repair": False,
        "outputs": 4,
        "x": 490,
        "y": 400,
        "wires": [
            ["update_angle_display"],
            ["connection_status"],
            ["error_display"],
            ["general_status"]
        ]
    },
    {
        "id": "update_angle_display",
        "type": "ui_gauge",
        "z": "servo_control_tab",
        "name": "Current Angle",
        "group": "ui_group_status",
        "order": 1,
        "width": 0,
        "height": 0,
        "gtype": "gage",
        "title": "Current Servo Angle",
        "label": "degrees",
        "format": "{{payload.angle}}",
        "min": 0,
        "max": 180,
        "colors": ["#00b500", "#e6e600", "#ca3838"],
        "seg1": "60",
        "seg2": "120",
        "x": 720,
        "y": 360,
        "wires": []
    },
    {
        "id": "connection_status",
        "type": "ui_led",
        "z": "servo_control_tab",
        "order": 2,
        "group": "ui_group_status",
        "width": 0,
        "height": 0,
        "label": "ESP32 Connection",
        "labelPlacement": "left",
        "labelAlignment": "left",
        "colorForValue": [
            {
                "color": "#ff0000",
                "value": "false",
                "valueType": "bool"
            },
            {
                "color": "#00ff00",
                "value": "true",
                "valueType": "bool"
            }
        ],
        "allowColorForValueInMessage": False,
        "name": "Connection LED",
        "x": 730,
        "y": 400,
        "wires": []
    },
    {
        "id": "error_display",
        "type": "ui_toast",
        "z": "servo_control_tab",
        "position": "top right",
        "displayTime": "3",
        "highlight": "",
        "sendall": True,
        "outputs": 0,
        "ok": "OK",
        "cancel": "",
        "raw": False,
        "topic": "Error",
        "name": "Error Toast",
        "x": 710,
        "y": 440,
        "wires": []
    },
    {
        "id": "general_status",
        "type": "ui_text",
        "z": "servo_control_tab",
        "group": "ui_group_status",
        "order": 3,
        "width": 0,
        "height": 0,
        "name": "Status Text",
        "label": "System Status",
        "format": "{{payload.status || 'Unknown'}}",
        "layout": "row-spread",
        "x": 710,
        "y": 480,
        "wires": []
    },
    {
        "id": "heartbeat_check",
        "type": "function",
        "z": "servo_control_tab",
        "name": "Heartbeat Monitor",
        "func": "// Store last heartbeat time\ncontext.lastHeartbeat = Date.now();\n\n// Set connection status to true\nmsg.payload = true;\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "x": 500,
        "y": 520,
        "wires": [["connection_status"]]
    },
    {
        "id": "heartbeat_timer",
        "type": "inject",
        "z": "servo_control_tab",
        "name": "Check Connection",
        "props": [
            {
                "p": "payload"
            }
        ],
        "repeat": "10",
        "crontab": "",
        "once": True,
        "onceDelay": "10",
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 150,
        "y": 520,
        "wires": [["connection_check"]]
    },
    {
        "id": "connection_check",
        "type": "function",
        "z": "servo_control_tab",
        "name": "Connection Timeout Check",
        "func": "// Check if last heartbeat was more than 60 seconds ago\nvar lastHeartbeat = context.get('lastHeartbeat') || 0;\nvar now = Date.now();\nvar timeDiff = now - lastHeartbeat;\n\nif (timeDiff > 60000) { // 60 seconds timeout\n    msg.payload = false; // Disconnected\n    node.warn('ESP32 connection timeout');\n} else {\n    msg.payload = true; // Connected\n}\n\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "x": 360,
        "y": 520,
        "wires": [["connection_status"]]
    }
]

def wait_for_nodered():
    """Wait for Node-RED to be ready"""
    print("Waiting for Node-RED to start...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{NODERED_URL}/flows", timeout=5)
            if response.status_code == 200:
                print("Node-RED is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("ERROR: Node-RED is not responding after 30 seconds")
    return False

def import_flow():
    """Import the servo control flow to Node-RED"""
    try:
        # Get current flows
        response = requests.get(f"{NODERED_URL}/flows")
        if response.status_code != 200:
            print(f"ERROR: Cannot get current flows: {response.status_code}")
            return False
        
        current_flows = response.json()
        
        # Add our flow to current flows
        new_flows = current_flows + SERVO_FLOW
        
        # Import the new flows
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{NODERED_URL}/flows",
            json=new_flows,
            headers=headers
        )
        
        if response.status_code == 204:
            print("✓ Servo control flow imported successfully!")
            return True
        else:
            print(f"ERROR: Failed to import flow: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"ERROR: Exception while importing flow: {e}")
        return False

def main():
    print("=== Node-RED Servo Control Flow Setup ===")
    
    # Wait for Node-RED to be ready
    if not wait_for_nodered():
        sys.exit(1)
    
    # Import the servo control flow
    if import_flow():
        print("\n✓ Setup complete!")
        print(f"Access your dashboard at: {NODERED_URL}/ui")
        print("The servo control dashboard should now be available.")
        print("\nFeatures:")
        print("- Angle slider (0-180 degrees)")
        print("- Preset buttons (Home, Left, Right)")
        print("- Real-time angle gauge")
        print("- Connection status LED")
        print("- Error notifications")
    else:
        print("\n✗ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

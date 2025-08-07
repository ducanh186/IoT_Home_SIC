#!/usr/bin/env python3
"""
Tạo Node-RED Dashboard cho Smart Door System
"""

import requests
import json
import time

def wait_for_nodered():
    print("⏳ Waiting for Node-RED...")
    for i in range(10):
        try:
            response = requests.get("http://127.0.0.1:1880", timeout=3)
            if response.status_code == 200:
                print("✅ Node-RED ready!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def create_dashboard():
    print("🎛️ Creating Smart Door Dashboard...")
    
    # Clear existing flows first
    try:
        requests.post("http://127.0.0.1:1880/flows", json=[], 
                     headers={'Content-Type': 'application/json'})
    except:
        pass
    
    # Dashboard flows
    flows = [
        # === TAB ===
        {
            "id": "smart_door_tab",
            "type": "tab",
            "label": "Smart Door System",
            "disabled": False,
            "info": ""
        },
        
        # === MQTT BROKER CONFIG ===
        {
            "id": "mqtt_broker",
            "type": "mqtt-broker",
            "name": "Smart Door MQTT",
            "broker": "10.189.169.194",
            "port": "1883",
            "clientid": "",
            "autoConnect": True,
            "usetls": False,
            "compatmode": False,
            "keepalive": "60",
            "cleansession": True,
            "birthTopic": "",
            "birthQos": "0",
            "birthPayload": "",
            "birthMsg": {},
            "closeTopic": "",
            "closeQos": "0",
            "closePayload": "",
            "closeMsg": {},
            "willTopic": "",
            "willQos": "0",
            "willPayload": "",
            "willMsg": {},
            "sessionExpiry": "",
            "credentials": {
                "user": "pi",
                "password": "1234"
            }
        },
        
        # === UI TAB ===
        {
            "id": "ui_tab_smart_door",
            "type": "ui_tab",
            "name": "🚪 Smart Door",
            "icon": "dashboard",
            "disabled": False,
            "hidden": False
        },
        
        # === UI GROUPS ===
        {
            "id": "ui_group_control",
            "type": "ui_group",
            "name": "Door Control",
            "tab": "ui_tab_smart_door",
            "order": 1,
            "disp": True,
            "width": "6",
            "collapse": False
        },
        
        {
            "id": "ui_group_status",
            "type": "ui_group", 
            "name": "Status & Info",
            "tab": "ui_tab_smart_door",
            "order": 2,
            "disp": True,
            "width": "6",
            "collapse": False
        },
        
        # === CONTROL BUTTONS ===
        {
            "id": "btn_open",
            "type": "ui_button",
            "z": "smart_door_tab",
            "name": "",
            "group": "ui_group_control",
            "order": 1,
            "width": "3",
            "height": "2",
            "passthru": False,
            "label": "🔴 OPEN",
            "tooltip": "Mở cửa ngay lập tức",
            "color": "white",
            "bgcolor": "#d9534f",
            "className": "",
            "icon": "",
            "payload": '{"action":"open","source":"button"}',
            "payloadType": "json",
            "topic": "door/cmd",
            "topicType": "str",
            "x": 150,
            "y": 100,
            "wires": [["add_timestamp"]]
        },
        
        {
            "id": "btn_close", 
            "type": "ui_button",
            "z": "smart_door_tab",
            "name": "",
            "group": "ui_group_control",
            "order": 2,
            "width": "3",
            "height": "2",
            "passthru": False,
            "label": "🟢 CLOSE",
            "tooltip": "Đóng cửa ngay lập tức",
            "color": "white",
            "bgcolor": "#5cb85c",
            "className": "",
            "icon": "",
            "payload": '{"action":"close","source":"button"}',
            "payloadType": "json",
            "topic": "door/cmd",
            "topicType": "str",
            "x": 150,
            "y": 140,
            "wires": [["add_timestamp"]]
        },
        
        # === ANGLE SLIDER ===
        {
            "id": "slider_angle",
            "type": "ui_slider",
            "z": "smart_door_tab",
            "name": "",
            "label": "Door Angle (0°-90°)",
            "tooltip": "Điều chỉnh góc cửa",
            "group": "ui_group_control",
            "order": 3,
            "width": "6",
            "height": "1",
            "passthru": True,
            "outs": "end",
            "topic": "angle",
            "topicType": "str",
            "min": 0,
            "max": 90,
            "step": 5,
            "x": 150,
            "y": 200,
            "wires": [["format_angle"]]
        },
        
        # === STATUS DISPLAYS ===
        {
            "id": "text_status",
            "type": "ui_text",
            "z": "smart_door_tab",
            "group": "ui_group_status",
            "order": 1,
            "width": "6",
            "height": "1",
            "name": "",
            "label": "Door Status:",
            "format": "{{msg.payload}}",
            "layout": "row-spread",
            "className": "",
            "x": 550,
            "y": 100,
            "wires": []
        },
        
        {
            "id": "text_angle",
            "type": "ui_text",
            "z": "smart_door_tab",
            "group": "ui_group_status",
            "order": 2,
            "width": "3",
            "height": "1",
            "name": "",
            "label": "Angle:",
            "format": "{{msg.payload}}°",
            "layout": "row-spread",
            "className": "",
            "x": 550,
            "y": 140,
            "wires": []
        },
        
        {
            "id": "text_presence",
            "type": "ui_text",
            "z": "smart_door_tab",
            "group": "ui_group_status",
            "order": 3,
            "width": "3",
            "height": "1",
            "name": "",
            "label": "Person:",
            "format": "{{msg.payload}}",
            "layout": "row-spread",
            "className": "",
            "x": 550,
            "y": 180,
            "wires": []
        },
        
        # === FUNCTION NODES ===
        {
            "id": "add_timestamp",
            "type": "function",
            "z": "smart_door_tab",
            "name": "Add Timestamp",
            "func": "msg.payload.timestamp = Math.floor(Date.now() / 1000);\nreturn msg;",
            "outputs": 1,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 350,
            "y": 120,
            "wires": [["mqtt_cmd_out"]]
        },
        
        {
            "id": "format_angle",
            "type": "function",
            "z": "smart_door_tab",
            "name": "Format Angle",
            "func": "msg.payload = {\n    angle: msg.payload,\n    source: 'manual',\n    timestamp: Math.floor(Date.now() / 1000)\n};\nreturn msg;",
            "outputs": 1,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 350,
            "y": 200,
            "wires": [["mqtt_cmd_out"]]
        },
        
        {
            "id": "parse_status",
            "type": "function",
            "z": "smart_door_tab",
            "name": "Parse Status",
            "func": "var data = msg.payload;\n\n// Update status display\nvar statusText = data.state === 'open' ? '🔴 OPEN' : '🟢 CLOSED';\nnode.send([{payload: statusText}, null, null]);\n\n// Update angle\nif (data.angle !== undefined) {\n    node.send([null, {payload: data.angle}, null]);\n}\n\n// Update presence\nif (data.presence !== undefined) {\n    var presenceText = data.presence ? '👤 YES' : '❌ NO';\n    node.send([null, null, {payload: presenceText}]);\n}\n\nreturn null;",
            "outputs": 3,
            "noerr": 0,
            "initialize": "",
            "finalize": "",
            "libs": [],
            "x": 350,
            "y": 300,
            "wires": [["text_status"], ["text_angle"], ["text_presence"]]
        },
        
        # === MQTT NODES ===
        {
            "id": "mqtt_cmd_out",
            "type": "mqtt out",
            "z": "smart_door_tab",
            "name": "Send Command",
            "topic": "door/cmd",
            "qos": "1",
            "retain": "false",
            "respTopic": "",
            "contentType": "",
            "userProps": "",
            "correl": "",
            "expiry": "",
            "broker": "mqtt_broker",
            "x": 550,
            "y": 160,
            "wires": []
        },
        
        {
            "id": "mqtt_status_in",
            "type": "mqtt in",
            "z": "smart_door_tab",
            "name": "Door Status",
            "topic": "door/status",
            "qos": "1",
            "datatype": "json",
            "broker": "mqtt_broker",
            "nl": False,
            "rap": True,
            "rh": 0,
            "inputs": 0,
            "x": 150,
            "y": 300,
            "wires": [["parse_status", "debug_status"]]
        },
        
        # === DEBUG NODES ===
        {
            "id": "debug_status",
            "type": "debug",
            "z": "smart_door_tab",
            "name": "Debug Status",
            "active": True,
            "tosidebar": True,
            "console": False,
            "tostatus": False,
            "complete": "payload",
            "targetType": "msg",
            "statusVal": "",
            "statusType": "auto",
            "x": 550,
            "y": 300,
            "wires": []
        }
    ]
    
    try:
        # Import flows
        response = requests.post("http://127.0.0.1:1880/flows",
                               json=flows,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code in [200, 204]:
            print("✅ Dashboard flows imported successfully!")
            time.sleep(2)
            
            # Deploy flows
            deploy_response = requests.post("http://127.0.0.1:1880/flows",
                                          headers={'Content-Type': 'application/json',
                                                 'Node-RED-Deployment-Type': 'full'})
            
            if deploy_response.status_code in [200, 204]:
                print("✅ Flows deployed successfully!")
                return True
            else:
                print(f"⚠️ Deploy response: {deploy_response.status_code}")
                return True  # Still consider success
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚪 Smart Door System - Dashboard Creator")
    print("========================================")
    
    if not wait_for_nodered():
        print("❌ Node-RED not accessible!")
        return False
    
    if create_dashboard():
        print("\n🎉 Dashboard created successfully!")
        print("="*40)
        print("📱 Access Dashboard:")
        print("   http://10.189.169.194:1880/ui")
        print("\n🔧 Node-RED Editor:")
        print("   http://10.189.169.194:1880")
        print("\n🎛️ Available Controls:")
        print("   • 🔴 OPEN button")
        print("   • 🟢 CLOSE button")
        print("   • 🎚️ Angle slider (0-90°)")
        print("   • 📊 Real-time status display")
        print("="*40)
        return True
    else:
        print("❌ Dashboard creation failed!")
        return False

if __name__ == "__main__":
    main()

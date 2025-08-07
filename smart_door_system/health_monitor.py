#!/usr/bin/env python3
"""
Smart Door System - Health Monitor
Giám sát trạng thái hệ thống và các services
"""

import subprocess
import socket
import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import sys

# Configuration
SERVICES = {
    "mosquitto": "MQTT Broker",
    "nodered": "Node-RED",
    "nginx": "Web Server"
}

PORTS = {
    1883: "MQTT",
    1880: "Node-RED", 
    80: "HTTP",
    443: "HTTPS"
}

MQTT_CONFIG = {
    "host": "10.189.169.194",
    "port": 1883,
    "user": "pi",
    "password": "1234"
}

def check_service_status(service_name):
    """Kiểm tra trạng thái service systemd"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False

def check_port(port, host="127.0.0.1"):
    """Kiểm tra port có mở không"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_mqtt_connection():
    """Test MQTT connection"""
    try:
        client = mqtt.Client(client_id="HealthCheck")
        client.username_pw_set(MQTT_CONFIG["user"], MQTT_CONFIG["password"])
        
        client.connect(MQTT_CONFIG["host"], MQTT_CONFIG["port"], 60)
        client.loop_start()
        time.sleep(1)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        return False

def check_nodered_dashboard():
    """Kiểm tra Node-RED dashboard"""
    try:
        response = requests.get("http://127.0.0.1:1880/ui", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def check_nginx_proxy():
    """Kiểm tra Nginx proxy"""
    try:
        response = requests.get("http://127.0.0.1:80", timeout=5, allow_redirects=False)
        return response.status_code in [200, 301, 302]
    except Exception:
        return False

def get_system_info():
    """Lấy thông tin hệ thống"""
    try:
        # CPU temperature
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        
        # Memory usage
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        
        mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1]) * 1024
        mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1]) * 1024
        mem_used = mem_total - mem_available
        mem_percent = (mem_used / mem_total) * 100
        
        # Disk usage
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        disk_info = result.stdout.split('\n')[1].split()
        disk_used = disk_info[4].rstrip('%')
        
        # Uptime
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
        
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        return {
            "cpu_temp": temp,
            "memory_percent": mem_percent,
            "disk_used_percent": int(disk_used),
            "uptime_hours": int(uptime_hours),
            "uptime_minutes": int(uptime_minutes)
        }
    except Exception as e:
        return {"error": str(e)}

def print_status_report():
    """In báo cáo trạng thái đầy đủ"""
    print("\n" + "="*60)
    print("🚪 SMART DOOR SYSTEM - HEALTH REPORT")
    print("="*60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # System Services
    print("🔧 SYSTEM SERVICES:")
    print("-" * 40)
    all_services_ok = True
    
    for service, description in SERVICES.items():
        status = check_service_status(service)
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {description:15} ({service})")
        if not status:
            all_services_ok = False
    
    print()
    
    # Network Ports
    print("🌐 NETWORK PORTS:")
    print("-" * 40)
    all_ports_ok = True
    
    for port, description in PORTS.items():
        status = check_port(port)
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {description:15} (:{port})")
        if not status:
            all_ports_ok = False
    
    print()
    
    # MQTT Connection
    print("📡 MQTT CONNECTION:")
    print("-" * 40)
    mqtt_ok = check_mqtt_connection()
    mqtt_icon = "✅" if mqtt_ok else "❌"
    print(f"  {mqtt_icon} MQTT Broker       (10.189.169.194:1883)")
    
    # Dashboard
    dashboard_ok = check_nodered_dashboard()
    dashboard_icon = "✅" if dashboard_ok else "❌"
    print(f"  {dashboard_icon} Node-RED Dashboard (http://10.189.169.194:1880/ui)")
    
    # Nginx Proxy
    proxy_ok = check_nginx_proxy()
    proxy_icon = "✅" if proxy_ok else "❌"
    print(f"  {proxy_icon} Nginx Proxy       (http://10.189.169.194)")
    
    print()
    
    # System Information
    print("💻 SYSTEM INFORMATION:")
    print("-" * 40)
    sys_info = get_system_info()
    
    if "error" not in sys_info:
        temp_status = "🟢" if sys_info["cpu_temp"] < 70 else "🟡" if sys_info["cpu_temp"] < 80 else "🔴"
        mem_status = "🟢" if sys_info["memory_percent"] < 70 else "🟡" if sys_info["memory_percent"] < 85 else "🔴"
        disk_status = "🟢" if sys_info["disk_used_percent"] < 80 else "🟡" if sys_info["disk_used_percent"] < 90 else "🔴"
        
        print(f"  {temp_status} CPU Temperature:  {sys_info['cpu_temp']:.1f}°C")
        print(f"  {mem_status} Memory Usage:     {sys_info['memory_percent']:.1f}%")
        print(f"  {disk_status} Disk Usage:       {sys_info['disk_used_percent']}%")
        print(f"  ⏱️  Uptime:           {sys_info['uptime_hours']}h {sys_info['uptime_minutes']}m")
    else:
        print(f"  ❌ Error getting system info: {sys_info['error']}")
    
    print()
    
    # Overall Status
    print("📊 OVERALL STATUS:")
    print("-" * 40)
    
    overall_ok = (all_services_ok and all_ports_ok and mqtt_ok and 
                  dashboard_ok and proxy_ok)
    
    if overall_ok:
        print("  🎉 ALL SYSTEMS OPERATIONAL!")
        print("  📱 Dashboard: https://10.189.169.194")
        print("  📱 Direct:    http://10.189.169.194:1880/ui")
    else:
        print("  ⚠️  SYSTEM ISSUES DETECTED!")
        print("  🔧 Check failed services above")
    
    print("="*60)
    
    return overall_ok

def quick_check():
    """Kiểm tra nhanh - chỉ show kết quả tổng"""
    services_ok = all(check_service_status(svc) for svc in SERVICES.keys())
    ports_ok = all(check_port(port) for port in PORTS.keys())
    mqtt_ok = check_mqtt_connection()
    
    overall_ok = services_ok and ports_ok and mqtt_ok
    
    status_icon = "✅" if overall_ok else "❌"
    print(f"{status_icon} Smart Door System: {'HEALTHY' if overall_ok else 'ISSUES DETECTED'}")
    
    return overall_ok

def monitor_continuous():
    """Giám sát liên tục"""
    print("🔍 Starting continuous monitoring (Press Ctrl+C to stop)...")
    print("Checking every 30 seconds...")
    
    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')
            overall_ok = quick_check()
            
            if not overall_ok:
                print(f"[{timestamp}] ⚠️  Issues detected - run full check for details")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped")

def restart_failed_services():
    """Restart các service bị lỗi"""
    print("🔧 Checking and restarting failed services...")
    
    for service in SERVICES.keys():
        if not check_service_status(service):
            print(f"🔄 Restarting {service}...")
            try:
                subprocess.run(["sudo", "systemctl", "restart", service], 
                             check=True, timeout=30)
                time.sleep(2)
                if check_service_status(service):
                    print(f"✅ {service} restarted successfully")
                else:
                    print(f"❌ {service} failed to restart")
            except Exception as e:
                print(f"❌ Error restarting {service}: {e}")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            quick_check()
        elif command == "monitor":
            monitor_continuous()
        elif command == "restart":
            restart_failed_services()
        elif command == "help":
            print("Smart Door System Health Monitor")
            print("Usage:")
            print("  python3 health_monitor.py        - Full status report")
            print("  python3 health_monitor.py quick  - Quick status check")
            print("  python3 health_monitor.py monitor - Continuous monitoring")
            print("  python3 health_monitor.py restart - Restart failed services")
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for available commands")
    else:
        print_status_report()

if __name__ == "__main__":
    main()

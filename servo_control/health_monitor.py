#!/usr/bin/env python3
"""
System Health Monitor for ESP32 Servo Control System
Monitors all system components and provides status dashboard
"""

import subprocess
import json
import time
import sys
from datetime import datetime
import socket

class SystemHealthMonitor:
    def __init__(self):
        self.services = {
            'mosquitto': 'MQTT Broker',
            'nodered': 'Node-RED Dashboard', 
            'nginx': 'Web Server'
        }
        
    def check_service_status(self, service_name):
        """Check if a systemd service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == 'active'
        except Exception:
            return False
            
    def check_port_open(self, port, host='localhost'):
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
            
    def get_service_memory_usage(self, service_name):
        """Get memory usage of a service"""
        try:
            result = subprocess.run(
                ['systemctl', 'show', service_name, '--property=MemoryCurrent'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if line.startswith('MemoryCurrent='):
                    memory_bytes = int(line.split('=')[1])
                    return memory_bytes / (1024 * 1024)  # Convert to MB
                    
        except Exception:
            pass
        return 0
        
    def get_system_info(self):
        """Get general system information"""
        info = {}
        
        try:
            # CPU usage
            result = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Cpu(s):' in line:
                    # Extract CPU usage percentage
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'us,' in part:
                            info['cpu_usage'] = float(parts[i-1])
                            break
                            
            # Memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                
            total_mem = 0
            free_mem = 0
            available_mem = 0
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    total_mem = int(line.split()[1]) / 1024  # Convert to MB
                elif line.startswith('MemFree:'):
                    free_mem = int(line.split()[1]) / 1024
                elif line.startswith('MemAvailable:'):
                    available_mem = int(line.split()[1]) / 1024
                    
            info['memory'] = {
                'total': round(total_mem, 1),
                'free': round(free_mem, 1),
                'available': round(available_mem, 1),
                'used_percent': round((total_mem - available_mem) / total_mem * 100, 1)
            }
            
            # Disk usage
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                info['disk'] = {
                    'total': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'used_percent': parts[4]
                }
                
            # System uptime
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                info['uptime'] = f"{hours}h {minutes}m"
                
            # Network interfaces
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            info['ip_addresses'] = result.stdout.strip().split()
            
        except Exception as e:
            info['error'] = str(e)
            
        return info
        
    def test_mqtt_connection(self):
        """Test MQTT broker connectivity"""
        try:
            import paho.mqtt.client as mqtt
            
            client = mqtt.Client()
            client.username_pw_set("pi", "1234")
            
            connected = False
            
            def on_connect(client, userdata, flags, rc):
                nonlocal connected
                connected = (rc == 0)
                
            client.on_connect = on_connect
            client.connect("localhost", 1883, 5)
            client.loop_start()
            
            # Wait for connection
            time.sleep(2)
            client.loop_stop()
            client.disconnect()
            
            return connected
            
        except ImportError:
            return "paho-mqtt not installed"
        except Exception as e:
            return str(e)
            
    def check_nodered_flows(self):
        """Check if Node-RED flows are loaded"""
        try:
            import requests
            response = requests.get("http://localhost:1880/flows", timeout=5)
            if response.status_code == 200:
                flows = response.json()
                servo_flows = [f for f in flows if 'servo' in str(f).lower()]
                return len(servo_flows) > 0
        except Exception:
            pass
        return False
        
    def generate_health_report(self):
        """Generate comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'ports': {},
            'system': self.get_system_info(),
            'mqtt_test': self.test_mqtt_connection(),
            'nodered_flows': self.check_nodered_flows()
        }
        
        # Check services
        for service, description in self.services.items():
            report['services'][service] = {
                'status': self.check_service_status(service),
                'description': description,
                'memory_mb': round(self.get_service_memory_usage(service), 1)
            }
            
        # Check ports
        important_ports = {
            80: 'HTTP (Nginx)',
            443: 'HTTPS (Nginx)', 
            1880: 'Node-RED',
            1883: 'MQTT'
        }
        
        for port, description in important_ports.items():
            report['ports'][port] = {
                'open': self.check_port_open(port),
                'description': description
            }
            
        return report
        
    def print_health_report(self, report):
        """Print formatted health report"""
        print("=" * 70)
        print("ESP32 SERVO CONTROL SYSTEM - HEALTH REPORT")
        print("=" * 70)
        print(f"Generated: {report['timestamp']}")
        print()
        
        # System Information
        print("🖥️  SYSTEM INFORMATION")
        print("-" * 30)
        sys_info = report['system']
        if 'cpu_usage' in sys_info:
            print(f"CPU Usage: {sys_info['cpu_usage']}%")
        if 'memory' in sys_info:
            mem = sys_info['memory']
            print(f"Memory: {mem['used_percent']}% used ({mem['total']} MB total)")
        if 'disk' in sys_info:
            disk = sys_info['disk']
            print(f"Disk: {disk['used_percent']} used ({disk['available']} available)")
        if 'uptime' in sys_info:
            print(f"Uptime: {sys_info['uptime']}")
        if 'ip_addresses' in sys_info:
            print(f"IP Addresses: {', '.join(sys_info['ip_addresses'])}")
        print()
        
        # Services Status
        print("🔧 SERVICES STATUS")
        print("-" * 30)
        for service, info in report['services'].items():
            status = "✅ RUNNING" if info['status'] else "❌ STOPPED"
            memory = f"({info['memory_mb']} MB)" if info['memory_mb'] > 0 else ""
            print(f"{info['description']}: {status} {memory}")
        print()
        
        # Ports Status
        print("🌐 NETWORK PORTS")
        print("-" * 30)
        for port, info in report['ports'].items():
            status = "✅ OPEN" if info['open'] else "❌ CLOSED"
            print(f"Port {port} ({info['description']}): {status}")
        print()
        
        # Additional Tests
        print("🧪 CONNECTIVITY TESTS")
        print("-" * 30)
        
        mqtt_status = report['mqtt_test']
        if mqtt_status is True:
            print("MQTT Broker: ✅ CONNECTION OK")
        elif mqtt_status is False:
            print("MQTT Broker: ❌ CONNECTION FAILED")
        else:
            print(f"MQTT Broker: ⚠️  {mqtt_status}")
            
        flows_status = report['nodered_flows']
        if flows_status:
            print("Node-RED Flows: ✅ SERVO FLOWS LOADED")
        else:
            print("Node-RED Flows: ⚠️  NO SERVO FLOWS FOUND")
        print()
        
        # Overall Health
        print("📊 OVERALL HEALTH")
        print("-" * 30)
        
        all_services_ok = all(info['status'] for info in report['services'].values())
        important_ports_ok = report['ports'][1883]['open'] and report['ports'][1880]['open']
        mqtt_ok = report['mqtt_test'] is True
        
        if all_services_ok and important_ports_ok and mqtt_ok:
            print("System Status: ✅ HEALTHY")
            print("All services are running and accessible.")
        else:
            print("System Status: ⚠️  ISSUES DETECTED")
            if not all_services_ok:
                print("- Some services are not running")
            if not important_ports_ok:
                print("- Important ports are not accessible")
            if not mqtt_ok:
                print("- MQTT connectivity issues")
        
        print("=" * 70)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output JSON format
        monitor = SystemHealthMonitor()
        report = monitor.generate_health_report()
        print(json.dumps(report, indent=2))
    else:
        # Output human-readable format
        monitor = SystemHealthMonitor()
        report = monitor.generate_health_report()
        monitor.print_health_report(report)
        
        if len(sys.argv) > 1 and sys.argv[1] == '--watch':
            print("\nWatching system health (Press Ctrl+C to stop)...")
            try:
                while True:
                    time.sleep(30)
                    print("\n" + "="*50)
                    print("UPDATED HEALTH REPORT")
                    print("="*50)
                    report = monitor.generate_health_report()
                    monitor.print_health_report(report)
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()

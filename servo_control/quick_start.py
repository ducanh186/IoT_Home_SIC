#!/usr/bin/env python3
"""
Quick Start Script for ESP32 Servo Control System
Run this script to quickly start/stop/restart the entire system
"""

import subprocess
import sys
import time
import os

class ServoControlManager:
    def __init__(self):
        self.services = ['mosquitto', 'nodered', 'nginx']
        
    def run_command(self, command, description=""):
        """Run a system command and return success status"""
        if description:
            print(f"⏳ {description}...")
            
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if description:
                    print(f"✅ {description} completed")
                return True, result.stdout
            else:
                if description:
                    print(f"❌ {description} failed: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} timed out")
            return False, "Timeout"
        except Exception as e:
            print(f"❌ {description} error: {e}")
            return False, str(e)
            
    def check_service_status(self, service):
        """Check if a service is running"""
        success, output = self.run_command(f"systemctl is-active {service}")
        return success and output.strip() == "active"
        
    def start_services(self):
        """Start all services"""
        print("🚀 Starting ESP32 Servo Control System...")
        print("=" * 50)
        
        for service in self.services:
            success, _ = self.run_command(
                f"sudo systemctl start {service}",
                f"Starting {service}"
            )
            
            if success:
                # Wait a moment and check if it's actually running
                time.sleep(2)
                if self.check_service_status(service):
                    print(f"✅ {service} is running")
                else:
                    print(f"⚠️  {service} started but may not be fully ready")
            else:
                print(f"❌ Failed to start {service}")
                
        print("\n🔍 Checking system status...")
        self.show_status()
        
    def stop_services(self):
        """Stop all services"""
        print("🛑 Stopping ESP32 Servo Control System...")
        print("=" * 50)
        
        for service in reversed(self.services):  # Stop in reverse order
            self.run_command(
                f"sudo systemctl stop {service}",
                f"Stopping {service}"
            )
            
        print("✅ All services stopped")
        
    def restart_services(self):
        """Restart all services"""
        print("🔄 Restarting ESP32 Servo Control System...")
        print("=" * 50)
        
        for service in self.services:
            self.run_command(
                f"sudo systemctl restart {service}",
                f"Restarting {service}"
            )
            time.sleep(2)
            
        print("\n🔍 Checking system status...")
        self.show_status()
        
    def show_status(self):
        """Show current status of all services"""
        print("\n📊 SYSTEM STATUS")
        print("=" * 30)
        
        all_running = True
        
        for service in self.services:
            if self.check_service_status(service):
                print(f"✅ {service}: RUNNING")
            else:
                print(f"❌ {service}: STOPPED")
                all_running = False
                
        # Check important ports
        print("\n🌐 NETWORK PORTS")
        print("-" * 20)
        
        import socket
        
        ports_to_check = {
            1883: "MQTT",
            1880: "Node-RED", 
            80: "HTTP",
            443: "HTTPS"
        }
        
        for port, name in ports_to_check.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    print(f"✅ Port {port} ({name}): OPEN")
                else:
                    print(f"❌ Port {port} ({name}): CLOSED")
                    all_running = False
            except:
                print(f"❌ Port {port} ({name}): ERROR")
                all_running = False
                
        # Get IP addresses
        success, ip_output = self.run_command("hostname -I")
        if success:
            ips = ip_output.strip().split()
            print(f"\n🌍 Access URLs:")
            for ip in ips[:2]:  # Show first 2 IPs
                print(f"   https://{ip}")
                print(f"   http://{ip}:1880/ui")
        
        print("\n" + "=" * 30)
        if all_running:
            print("🎉 System is HEALTHY and ready to use!")
        else:
            print("⚠️  System has ISSUES - check the logs")
            
    def show_logs(self, service=None):
        """Show logs for a service"""
        if service and service in self.services:
            print(f"📋 Showing logs for {service}...")
            os.system(f"sudo journalctl -u {service} -n 20 --no-pager")
        else:
            for svc in self.services:
                print(f"\n📋 {svc} logs (last 10 lines):")
                print("-" * 40)
                os.system(f"sudo journalctl -u {svc} -n 10 --no-pager")
                
    def install_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        dependencies = [
            "paho-mqtt",
            "requests"
        ]
        
        for dep in dependencies:
            success, _ = self.run_command(
                f"pip3 install {dep}",
                f"Installing {dep}"
            )
            
        print("✅ Dependencies installation completed")

def print_usage():
    """Print usage information"""
    print("ESP32 Servo Control System Manager")
    print("=" * 40)
    print("Usage: python3 quick_start.py [command]")
    print()
    print("Commands:")
    print("  start     - Start all services")
    print("  stop      - Stop all services") 
    print("  restart   - Restart all services")
    print("  status    - Show system status")
    print("  logs      - Show service logs")
    print("  logs <service> - Show logs for specific service")
    print("  install   - Install Python dependencies")
    print("  help      - Show this help")
    print()
    print("Examples:")
    print("  python3 quick_start.py start")
    print("  python3 quick_start.py status")
    print("  python3 quick_start.py logs mosquitto")

def main():
    manager = ServoControlManager()
    
    if len(sys.argv) < 2:
        print_usage()
        return
        
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_services()
        
    elif command == "stop":
        manager.stop_services()
        
    elif command == "restart":
        manager.restart_services()
        
    elif command == "status":
        manager.show_status()
        
    elif command == "logs":
        if len(sys.argv) > 2:
            service = sys.argv[2]
            manager.show_logs(service)
        else:
            manager.show_logs()
            
    elif command == "install":
        manager.install_dependencies()
        
    elif command == "help":
        print_usage()
        
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()

if __name__ == "__main__":
    main()

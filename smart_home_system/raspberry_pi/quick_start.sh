#!/bin/bash

# Quick Start Script cho IoT Smart Home System
# Script khởi chạy nhanh toàn bộ hệ thống

echo "🚀 IoT Smart Home System - Quick Start"
echo "======================================"

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Vui lòng chạy với quyền sudo:"
    echo "   sudo bash quick_start.sh"
    exit 1
fi

# Kiểm tra kết nối internet
echo "🌐 Checking internet connection..."
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Internet connection OK"
else
    echo "❌ No internet connection. Please check your network."
    exit 1
fi

# Cập nhật hệ thống
echo "📦 Updating system packages..."
apt update -qq

# Kiểm tra và cài đặt các dependency cần thiết
echo "🔧 Installing required packages..."
apt install -y mosquitto mosquitto-clients python3-pip nodejs npm sqlite3

# Cài đặt Python packages
echo "🐍 Installing Python packages..."
pip3 install flask flask-socketio paho-mqtt

# Cài đặt Node-RED
echo "🔴 Installing Node-RED..."
npm install -g --unsafe-perm node-red
npm install -g node-red-dashboard

# Tạo thư mục làm việc
echo "📁 Creating working directories..."
mkdir -p /home/pi/smart_home/{logs,database,config}
chown -R pi:pi /home/pi/smart_home

# Copy files đến vị trí hệ thống
echo "📋 Setting up system files..."
cp /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/*.py /home/pi/smart_home/
cp -r /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/templates /home/pi/smart_home/

# Cấu hình MQTT
echo "🔒 Configuring MQTT broker..."
cat > /etc/mosquitto/conf.d/smart_home.conf << EOF
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

listener 9001
protocol websockets
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

# Tạo MQTT user
echo "👤 Creating MQTT user..."
mosquitto_passwd -c -b /etc/mosquitto/passwd pi101 1234

# Tạo systemd services
echo "⚙️ Creating system services..."

# MQTT Receiver Service
cat > /etc/systemd/system/smart-home-mqtt.service << EOF
[Unit]
Description=Smart Home MQTT Receiver
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart_home
ExecStart=/usr/bin/python3 mqtt_receiver.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Web Dashboard Service  
cat > /etc/systemd/system/smart-home-web.service << EOF
[Unit]
Description=Smart Home Web Dashboard
After=network.target smart-home-mqtt.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart_home
ExecStart=/usr/bin/python3 web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Node-RED Service
cat > /etc/systemd/system/node-red.service << EOF
[Unit]
Description=Node-RED
After=syslog.target network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/local/bin/node-red
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd và enable services
echo "🔄 Enabling services..."
systemctl daemon-reload
systemctl enable mosquitto
systemctl enable smart-home-mqtt
systemctl enable smart-home-web  
systemctl enable node-red

# Khởi động services
echo "▶️ Starting services..."
systemctl restart mosquitto
sleep 5
systemctl start smart-home-mqtt
sleep 3
systemctl start smart-home-web
systemctl start node-red

# Kiểm tra trạng thái services
echo "📊 Checking service status..."
echo ""

services=("mosquitto" "smart-home-mqtt" "smart-home-web" "node-red")
all_running=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Failed"
        all_running=false
    fi
done

echo ""

if [ "$all_running" = true ]; then
    echo "🎉 ALL SERVICES RUNNING SUCCESSFULLY!"
    echo ""
    echo "🌐 Access your dashboards:"
    echo "   📱 Web Dashboard: http://raspberrypi.local:5000"
    echo "   🔴 Node-RED: http://raspberrypi.local:1880"
    echo "   ⚙️ Node-RED Dashboard: http://raspberrypi.local:1880/ui"
    echo ""
    echo "📋 MQTT Info:"
    echo "   🏠 Broker: raspberrypi.local:1883"
    echo "   🌐 WebSocket: ws://raspberrypi.local:9001"
    echo "   👤 Username: pi101"
    echo "   🔑 Password: 1234"
    echo ""
    echo "📊 Monitor services:"
    echo "   sudo systemctl status mosquitto"
    echo "   sudo systemctl status smart-home-mqtt"
    echo "   sudo systemctl status smart-home-web"
    echo "   sudo systemctl status node-red"
    echo ""
    echo "🔍 View logs:"
    echo "   sudo journalctl -u smart-home-mqtt -f"
    echo "   sudo journalctl -u smart-home-web -f"
    echo ""
    echo "🏠 Now upload Arduino code to your ESP32 devices!"
else
    echo "⚠️ Some services failed to start. Check logs:"
    echo "   sudo journalctl -u mosquitto"
    echo "   sudo journalctl -u smart-home-mqtt"
    echo "   sudo journalctl -u smart-home-web"
    echo "   sudo journalctl -u node-red"
fi

echo ""
echo "🎯 Quick Start completed!"

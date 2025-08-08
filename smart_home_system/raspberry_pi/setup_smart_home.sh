#!/bin/bash

# IoT Home Smart System Setup Script
# Cài đặt và cấu hình MQTT broker, Node-RED và các services cần thiết

echo "🏠 IoT Home Smart System Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system
print_step "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_step "Installing required packages..."
apt install -y mosquitto mosquitto-clients python3-pip nodejs npm sqlite3

# Install Python packages
print_step "Installing Python packages..."
pip3 install paho-mqtt flask flask-socketio sqlite3

# Configure Mosquitto MQTT Broker
print_step "Configuring MQTT Broker..."

# Create mosquitto config directory if not exists
mkdir -p /etc/mosquitto/conf.d

# Create password file
mosquitto_passwd -c -b /etc/mosquitto/passwd pi101 1234

# Create mosquitto configuration
cat > /etc/mosquitto/conf.d/smart_home.conf << EOL
# Smart Home MQTT Configuration
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd

# WebSocket support for web dashboard
listener 9001 0.0.0.0
protocol websockets

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Client connection
max_connections 50
EOL

# Set permissions for mosquitto
chown mosquitto:mosquitto /etc/mosquitto/passwd
chmod 600 /etc/mosquitto/passwd

# Enable and start mosquitto
systemctl enable mosquitto
systemctl restart mosquitto

print_status "MQTT Broker configured and started"

# Install Node-RED
print_step "Installing Node-RED..."
npm install -g --unsafe-perm node-red

# Create Node-RED systemd service
cat > /etc/systemd/system/nodered.service << EOL
[Unit]
Description=Node-RED
After=syslog.target network.target

[Service]
ExecStart=/usr/bin/node-red --max-old-space-size=128 -v
Restart=on-failure
KillSignal=SIGINT

# User/group to run as
User=pi
Group=pi

# Where to run from
WorkingDirectory=/home/pi

# Environment variables
Environment="NODE_OPTIONS=--max_old_space_size=128"
Environment="NODE_RED_OPTIONS=-v"

[Install]
WantedBy=multi-user.target
EOL

# Enable Node-RED service
systemctl daemon-reload
systemctl enable nodered

# Create Node-RED directory structure
sudo -u pi mkdir -p /home/pi/.node-red

# Install Node-RED nodes for MQTT and dashboard
print_step "Installing Node-RED dashboard nodes..."
sudo -u pi npm install --prefix /home/pi/.node-red node-red-dashboard node-red-contrib-ui-led

# Configure hostname resolution
print_step "Configuring hostname resolution..."

# Enable mDNS for hostname resolution
apt install -y avahi-daemon avahi-utils

# Ensure hostname is set correctly
hostnamectl set-hostname raspberrypi

# Add hostname to /etc/hosts if not exists
if ! grep -q "raspberrypi.local" /etc/hosts; then
    echo "127.0.1.1    raspberrypi.local" >> /etc/hosts
fi

# Create smart home data directory
print_step "Creating project directories..."
sudo -u pi mkdir -p /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/logs
sudo -u pi mkdir -p /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/data

# Make Python scripts executable
chmod +x /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/mqtt_receiver.py

# Create systemd service for MQTT receiver
cat > /etc/systemd/system/smart-home-receiver.service << EOL
[Unit]
Description=Smart Home MQTT Data Receiver
After=mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi
ExecStart=/usr/bin/python3 /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/mqtt_receiver.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Enable the service
systemctl daemon-reload
systemctl enable smart-home-receiver

# Create log rotation for smart home logs
cat > /etc/logrotate.d/smart-home << EOL
/home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
EOL

print_step "Starting services..."

# Start services
systemctl start mosquitto
systemctl start nodered
systemctl start smart-home-receiver

# Wait a moment for services to start
sleep 5

# Check service status
print_step "Checking service status..."

if systemctl is-active --quiet mosquitto; then
    print_status "✅ MQTT Broker (Mosquitto) is running"
else
    print_error "❌ MQTT Broker failed to start"
fi

if systemctl is-active --quiet nodered; then
    print_status "✅ Node-RED is running"
else
    print_error "❌ Node-RED failed to start"
fi

if systemctl is-active --quiet smart-home-receiver; then
    print_status "✅ Smart Home MQTT Receiver is running"
else
    print_error "❌ Smart Home MQTT Receiver failed to start"
fi

# Display network information
print_step "Network Information:"
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "📍 Raspberry Pi IP: $IP_ADDRESS"
echo "🌐 Hostname: raspberrypi.local"
echo "📡 MQTT Broker: $IP_ADDRESS:1883 (or raspberrypi.local:1883)"
echo "🌐 MQTT WebSocket: $IP_ADDRESS:9001"
echo "🎛️ Node-RED Dashboard: http://$IP_ADDRESS:1880 (or http://raspberrypi.local:1880)"

print_step "Testing MQTT connection..."
if mosquitto_pub -h localhost -p 1883 -u pi101 -P 1234 -t test/connection -m "Hello from Raspberry Pi" 2>/dev/null; then
    print_status "✅ MQTT connection test successful"
else
    print_error "❌ MQTT connection test failed"
fi

# Create a simple test script
cat > /home/pi/test_mqtt.sh << EOL
#!/bin/bash
echo "Testing MQTT connection..."
echo "Publishing test message..."
mosquitto_pub -h localhost -p 1883 -u pi101 -P 1234 -t test/message -m "Test from \$(date)"

echo "Subscribing to test topic (press Ctrl+C to stop):"
mosquitto_sub -h localhost -p 1883 -u pi101 -P 1234 -t test/message
EOL

chmod +x /home/pi/test_mqtt.sh
chown pi:pi /home/pi/test_mqtt.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo "1. Upload Arduino code to your ESP32 devices"
echo "2. Update WiFi credentials in Arduino code if needed"
echo "3. Access Node-RED dashboard at: http://raspberrypi.local:1880"
echo "4. Test MQTT with: /home/pi/test_mqtt.sh"
echo ""
echo "📁 Project Structure:"
echo "   /home/pi/project/IoT_Home_SIC/smart_home_system/"
echo "   ├── bedroom/              (Arduino code for bedroom nodes)"
echo "   ├── livingroom/           (Arduino code for livingroom nodes)"
echo "   ├── raspberry_pi/         (Python scripts and data)"
echo "   └── config/               (Configuration files)"
echo ""
echo "🔧 Service Management:"
echo "   sudo systemctl status mosquitto"
echo "   sudo systemctl status nodered"
echo "   sudo systemctl status smart-home-receiver"
echo ""
print_status "Smart Home IoT system is ready to use! 🏠✨"

#!/bin/bash

# Smart Door System Setup Script for Raspberry Pi 5
# Cài đặt tự động tất cả services cần thiết

echo "🚪 Setting up Smart Door System on Raspberry Pi 5..."
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y mosquitto mosquitto-clients nodejs npm nginx openssl python3-pip

# Setup Mosquitto MQTT Broker
echo "🌐 Configuring Mosquitto MQTT Broker..."
sudo systemctl stop mosquitto

# Create MQTT password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd pi
echo "1234" | sudo mosquitto_passwd -b /etc/mosquitto/passwd pi 1234

# Configure Mosquitto
sudo tee /etc/mosquitto/conf.d/smart_door.conf > /dev/null << 'EOF'
# Smart Door System MQTT Configuration
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information
log_timestamp true

# Security
max_connections 100
max_inflight_messages 20
max_queued_messages 100
message_size_limit 1024

# Persistence
persistence true
persistence_location /var/lib/mosquitto/
persistence_file mosquitto.db
autosave_interval 1800
EOF

# Create log directory
sudo mkdir -p /var/log/mosquitto
sudo chown mosquitto:mosquitto /var/log/mosquitto

# Start Mosquitto
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

echo "✅ Mosquitto MQTT Broker configured"

# Install Node-RED
echo "🔴 Installing Node-RED..."
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)

# Install Node-RED dashboard and additional nodes
echo "📊 Installing Node-RED dashboard nodes..."
cd /home/pi/.node-red
npm install node-red-dashboard
npm install node-red-contrib-ui-led
npm install node-red-node-random
npm install node-red-contrib-moment
npm install node-red-contrib-simple-gate

# Enable and start Node-RED
sudo systemctl enable nodered.service
sudo systemctl start nodered.service

echo "✅ Node-RED installed and configured"

# Configure Nginx
echo "🌐 Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/smart_door > /dev/null << 'EOF'
server {
    listen 80;
    server_name 10.189.169.194;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name 10.189.169.194;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/smart_door.crt;
    ssl_certificate_key /etc/ssl/private/smart_door.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://127.0.0.1:1880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket support for Node-RED
    location /comms {
        proxy_pass http://127.0.0.1:1880/comms;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Generate self-signed SSL certificate
echo "🔐 Generating SSL certificate..."
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/smart_door.key \
    -out /etc/ssl/certs/smart_door.crt \
    -subj "/C=VN/ST=HCM/L=HCM/O=SmartDoor/CN=10.189.169.194"

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/smart_door /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "✅ Nginx configured with SSL"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install paho-mqtt requests

# Create systemd service for door monitor
echo "🔧 Creating system monitor service..."
sudo tee /etc/systemd/system/smart-door-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Smart Door System Monitor
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/IoT_Home_SIC/smart_door_system
ExecStart=/usr/bin/python3 /home/pi/IoT_Home_SIC/smart_door_system/door_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create firewall rules
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 1880/tcp  # Node-RED
sudo ufw allow 1883/tcp  # MQTT
sudo ufw --force enable

# Set static IP (if not already set)
echo "🌐 Checking network configuration..."
if ! grep -q "10.189.169.194" /etc/dhcpcd.conf; then
    echo "Setting static IP..."
    sudo tee -a /etc/dhcpcd.conf > /dev/null << 'EOF'

# Smart Door System static IP
interface wlan0
static ip_address=10.189.169.194/24
static routers=10.189.169.1
static domain_name_servers=8.8.8.8 8.8.4.4
EOF
fi

# Create log directory
sudo mkdir -p /var/log/smart_door
sudo chown pi:pi /var/log/smart_door

echo ""
echo "🎉 Smart Door System setup completed!"
echo "======================================"
echo ""
echo "📊 Dashboard Access:"
echo "  HTTPS: https://10.189.169.194"
echo "  HTTP:  http://10.189.169.194:1880/ui"
echo ""
echo "🔧 MQTT Broker:"
echo "  Host: 10.189.169.194:1883"
echo "  User: pi"
echo "  Pass: 1234"
echo ""
echo "📝 Next Steps:"
echo "  1. Reboot Pi to apply network settings: sudo reboot"
echo "  2. Upload ESP32 code: esp32_smart_door.ino"
echo "  3. Import Node-RED flows: python3 setup_flows.py"
echo "  4. Connect hardware (servo + sensor)"
echo ""
echo "🔍 Check Status:"
echo "  sudo systemctl status mosquitto"
echo "  sudo systemctl status nodered"
echo "  sudo systemctl status nginx"
echo ""

# Final status check
echo "🔍 Current Service Status:"
echo "========================="
sudo systemctl is-active mosquitto && echo "✅ Mosquitto: Running" || echo "❌ Mosquitto: Failed"
sudo systemctl is-active nodered && echo "✅ Node-RED: Running" || echo "❌ Node-RED: Failed"
sudo systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Failed"

echo ""
echo "📋 Setup completed successfully!"
echo "Remember to reboot the system to apply all changes."

#!/bin/bash

# ESP32 Servo Control System Setup Script for Raspberry Pi 5
# This script installs and configures all required services

echo "=== ESP32 Servo Control System Setup ==="
echo "Installing Mosquitto MQTT Broker, Node-RED, and Nginx..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Mosquitto MQTT Broker
echo "Installing Mosquitto MQTT Broker..."
sudo apt install mosquitto mosquitto-clients -y

# Configure Mosquitto
echo "Configuring Mosquitto..."
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup

sudo tee /etc/mosquitto/mosquitto.conf > /dev/null <<EOF
# Mosquitto Configuration for ESP32 Servo Control
pid_file /run/mosquitto/mosquitto.pid

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

connection_messages true
log_timestamp true

# Network settings
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd

# WebSocket support for Node-RED dashboard
listener 9001
protocol websockets
EOF

# Create MQTT user
echo "Creating MQTT user 'pi'..."
sudo mosquitto_passwd -c /etc/mosquitto/passwd pi

# Enable and start Mosquitto
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

# Install Node.js and npm (required for Node-RED)
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Node-RED
echo "Installing Node-RED..."
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)

# Install Node-RED additional nodes
echo "Installing Node-RED dashboard and MQTT nodes..."
cd ~/.node-red
npm install node-red-dashboard
npm install node-red-contrib-ui-led

# Enable Node-RED service
sudo systemctl enable nodered.service

# Install Nginx
echo "Installing Nginx..."
sudo apt install nginx -y

# Configure Nginx as reverse proxy
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/servo-control > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    # SSL Configuration (self-signed for local use)
    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Proxy to Node-RED
    location / {
        proxy_pass http://127.0.0.1:1880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support for Node-RED
    location /ws/ {
        proxy_pass http://127.0.0.1:1880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Create SSL directory and generate self-signed certificate
echo "Creating SSL certificates..."
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key \
    -out /etc/nginx/ssl/nginx.crt \
    -subj "/C=VN/ST=HCM/L=HoChiMinh/O=IoT/OU=Home/CN=raspberrypi"

# Enable the site
sudo ln -sf /etc/nginx/sites-available/servo-control /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Enable and start services
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl start nodered

echo "=== Installation Complete! ==="
echo ""
echo "Services status:"
echo "- Mosquitto MQTT: $(sudo systemctl is-active mosquitto)"
echo "- Node-RED: $(sudo systemctl is-active nodered)"
echo "- Nginx: $(sudo systemctl is-active nginx)"
echo ""
echo "Access your dashboard at: https://$(hostname -I | awk '{print $1}')"
echo "Node-RED editor: http://$(hostname -I | awk '{print $1}'):1880"
echo ""
echo "Next steps:"
echo "1. Configure your ESP32 with the correct WiFi and MQTT settings"
echo "2. Import the Node-RED flow (use setup_nodered_flow.py)"
echo "3. Test the servo control through the web dashboard"

#!/bin/bash

# Clean Up Old Project Files
# Script để dọn dẹp các file cũ không cần thiết

echo "🧹 Cleaning up old project files..."

# Remove old sensor_MQTT files (keep essential ones)
echo "📂 Cleaning sensor_MQTT directory..."
cd /home/pi/project/IoT_Home_SIC/sensor_MQTT

# Keep only essential files, remove duplicates
if [ -f "Dubaotroimua.ino" ]; then
    echo "  🗑️ Removing Dubaotroimua.ino (deprecated)"
    rm -f Dubaotroimua.ino
fi

if [ -f "node5.ino" ]; then
    echo "  🗑️ Removing node5.ino (not used in new structure)"
    rm -f node5.ino
fi

if [ -f "receive_smart_trash_can" ]; then
    echo "  🗑️ Removing receive_smart_trash_can (not used)"
    rm -f receive_smart_trash_can
fi

# Archive the old node1.ino for reference
if [ -f "node1.ino" ]; then
    echo "  📦 Archiving old node1.ino"
    mv node1.ino node1_old_backup.ino
fi

# Keep receive_script.py as reference
if [ -f "receive_script.py" ]; then
    echo "  📦 Archiving old receive_script.py"
    mv receive_script.py receive_script_old_backup.py
fi

# Clean smart_door_system directory
echo "📂 Cleaning smart_door_system directory..."
cd /home/pi/project/IoT_Home_SIC/smart_door_system

# Archive old files
if [ -f "esp32_smart_door.ino" ]; then
    echo "  📦 Archiving old esp32_smart_door.ino"
    mv esp32_smart_door.ino esp32_smart_door_old_backup.ino
fi

if [ -f "esp32_smart_door.ino.backup" ]; then
    echo "  🗑️ Removing redundant backup file"
    rm -f esp32_smart_door.ino.backup
fi

# Keep useful scripts but rename them
if [ -f "test_door_client.py" ]; then
    echo "  📦 Archiving test_door_client.py"
    mv test_door_client.py test_door_client_old_backup.py
fi

if [ -f "create_dashboard.py" ]; then
    echo "  🗑️ Removing old create_dashboard.py (replaced by new web dashboard)"
    rm -f create_dashboard.py
fi

if [ -f "health_monitor.py" ]; then
    echo "  🗑️ Removing old health_monitor.py (integrated into new system)"
    rm -f health_monitor.py
fi

if [ -f "setup_smart_door.sh" ]; then
    echo "  📦 Archiving old setup_smart_door.sh"
    mv setup_smart_door.sh setup_smart_door_old_backup.sh
fi

# Clean servo_control directory
echo "📂 Cleaning servo_control directory..."
cd /home/pi/project/IoT_Home_SIC/servo_control

# Remove all files as they're not needed in new structure
echo "  🗑️ Removing servo_control directory contents (integrated into smart_home_system)"
rm -f *.ino *.py *.json *.sh *.conf *.h

# Create archive directory for old files
echo "📦 Creating archive directory..."
mkdir -p /home/pi/project/IoT_Home_SIC/archive_old_files

# Move any remaining important files to archive
cd /home/pi/project/IoT_Home_SIC

if [ -f "sensor_MQTT/ESP32_Wiring_Diagram.md" ]; then
    cp sensor_MQTT/ESP32_Wiring_Diagram.md archive_old_files/
fi

if [ -f "smart_door_system/ESP32_Wiring_Diagram.md" ]; then
    cp smart_door_system/ESP32_Wiring_Diagram.md archive_old_files/
fi

if [ -f "smart_door_system/README.md" ]; then
    cp smart_door_system/README.md archive_old_files/old_smart_door_README.md
fi

# Set proper permissions for new system
echo "🔐 Setting proper permissions..."
chown -R pi:pi /home/pi/project/IoT_Home_SIC/smart_home_system
chmod +x /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/*.py
chmod +x /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/*.sh

echo "✅ Cleanup completed!"
echo ""
echo "📋 Summary:"
echo "  ✅ Old files archived in: archive_old_files/"
echo "  ✅ New clean structure ready in: smart_home_system/"
echo "  ✅ Arduino code ready in: smart_home_system/bedroom/ and smart_home_system/livingroom/"
echo "  ✅ Raspberry Pi scripts ready in: smart_home_system/raspberry_pi/"
echo ""
echo "🚀 Next step: Run the setup script:"
echo "  sudo bash /home/pi/project/IoT_Home_SIC/smart_home_system/raspberry_pi/setup_smart_home.sh"

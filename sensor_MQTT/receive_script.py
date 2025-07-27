import paho.mqtt.client as mqtt
import json
from datetime import datetime

MQTT_ADDRESS = '192.168.1.3'  # IP Raspberry Pi 5 của bạn
MQTT_USER = 'pi101'           # user đã tạo trong Mosquitto
MQTT_PASSWORD = '1234'        # mật khẩu tương ứng

# MQTT Topics từ ESP32 NodeMCU - tương thích với cảm biến MQ 2 chân
MQTT_TOPIC_TEMP = 'temperature'
MQTT_TOPIC_HUMD = 'humidity'
MQTT_TOPIC_GAS_ANALOG = 'gas_analog'      # Giá trị analog MQ (0-4095)
MQTT_TOPIC_GAS_DIGITAL = 'gas_digital'    # Trạng thái digital MQ
MQTT_TOPIC_GAS_STATUS = 'gas_status'      # SAFE/WARNING/DANGER
MQTT_TOPIC_FIRE = 'fire_detected'

# Store latest sensor data from ESP32 - cập nhật cho MQ 2 chân
sensor_data = {
    'temperature': None,
    'humidity': None,
    'gas_analog': None,        # Thêm gas analog
    'gas_digital': None,       # Thêm gas digital  
    'gas_status': None,
    'fire_detected': None,
    'last_update': None
}

def on_connect(client, userdata, flags, rc):
    print('🔗 Connected to MQTT broker with result code ' + str(rc))
    
    # Subscribe to all ESP32 sensor topics - cập nhật cho MQ 2 chân
    topics = [MQTT_TOPIC_TEMP, MQTT_TOPIC_HUMD, MQTT_TOPIC_GAS_ANALOG, 
              MQTT_TOPIC_GAS_DIGITAL, MQTT_TOPIC_GAS_STATUS, MQTT_TOPIC_FIRE]
    
    for topic in topics:
        client.subscribe(topic)
        print(f"  ✅ Subscribed to: {topic}")
    
    print("📡 Ready to receive data from ESP32 NodeMCU...")

def display_sensor_summary():
    """Display current sensor status from ESP32"""
    print("\n" + "="*60)
    print("      🏠 ESP32 SAFETY MONITORING SYSTEM STATUS")
    print("="*60)
    print(f"🕒 Last Update: {sensor_data['last_update']}")
    print(f"🌡️  Temperature: {sensor_data['temperature']}°C")
    print(f"💧 Humidity: {sensor_data['humidity']}%")
    print(f"💨 Gas Analog: {sensor_data['gas_analog']}/4095 ({sensor_data['gas_status']})")
    print(f"🔘 Gas Digital: {sensor_data['gas_digital']}")
    print(f"🔥 Fire Status: {sensor_data['fire_detected']}")
    
    # Alert status with emojis
    if sensor_data['fire_detected'] == 'FIRE_DETECTED':
        print("🚨🔥 FIRE ALERT! IMMEDIATE ACTION REQUIRED! 🔥🚨")
    elif sensor_data['gas_status'] == 'DANGER':
        print("⚠️🚨 GAS DANGER ALERT! EVACUATE AREA! 🚨⚠️")
    elif sensor_data['gas_status'] == 'WARNING':
        print("⚠️⚠️ GAS WARNING - CHECK VENTILATION ⚠️⚠️")
    else:
        print("✅✅ All systems normal - Environment safe ✅✅")
    print("="*60)

def process_sensor_data(topic, value):
    """Process sensor data from ESP32 and trigger alerts"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if topic == MQTT_TOPIC_TEMP:
        sensor_data['temperature'] = float(value)
    elif topic == MQTT_TOPIC_HUMD:
        sensor_data['humidity'] = float(value)
    elif topic == MQTT_TOPIC_GAS_ANALOG:
        sensor_data['gas_analog'] = int(value)
    elif topic == MQTT_TOPIC_GAS_DIGITAL:
        sensor_data['gas_digital'] = value
    elif topic == MQTT_TOPIC_GAS_STATUS:
        sensor_data['gas_status'] = value
        # Critical gas status logging
        if value == 'DANGER':
            print(f"🚨 CRITICAL GAS ALERT: {value} level detected at {timestamp}")
        elif value == 'WARNING':
            print(f"⚠️  GAS WARNING: {value} level detected at {timestamp}")
    elif topic == MQTT_TOPIC_FIRE:
        sensor_data['fire_detected'] = value
        # Fire detection logging
        if value == 'FIRE_DETECTED':
            print(f"🔥🚨 FIRE EMERGENCY: Fire detected at {timestamp}")
    
    sensor_data['last_update'] = timestamp
    
    # Display summary for critical alerts
    if topic in [MQTT_TOPIC_FIRE, MQTT_TOPIC_GAS_STATUS]:
        display_sensor_summary()

def on_message(client, userdata, msg):
    topic = msg.topic
    value = msg.payload.decode('utf-8')
    
    # Log all incoming data with timestamp
    print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] {topic}: {value}")
    
    # Process the ESP32 data
    process_sensor_data(topic, value)

def main():
    print('🏠 ESP32 IoT Safety Monitoring System Starting...')
    print('🔧 Hardware: ESP32 NodeMCU + Raspberry Pi 5')
    print('📡 Connecting to MQTT broker on Raspberry Pi 5...')
    
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_ADDRESS, 1883)
        print('✅ Connected to MQTT broker successfully!')
        print('🔄 Listening for sensor data from ESP32...\n')
        
        # Display initial status
        print("📊 Monitoring the following sensors:")
        print("  🌡️  DHT11 - Temperature & Humidity")
        print("  💨 MQ Sensor - Gas Detection (Analog + Digital)")
        print("  🔥 Flame Sensor - Fire Detection")
        print("  💡 LED Indicators - Status Display")
        print("  🔊 Buzzer - Audio Alerts (10 beeps pattern)")
        print("\n" + "="*50)
        
        mqtt_client.loop_forever()
        
    except KeyboardInterrupt:
        print('\n🛑 System stopped by user')
        print('📴 Disconnecting from MQTT broker...')
        mqtt_client.disconnect()
        print('✅ Safely disconnected')
        
    except Exception as e:
        print(f'❌ Connection error: {e}')
        print('💡 Check if MQTT broker is running on Raspberry Pi 5')
        print('💡 Verify ESP32 is connected and sending data')

if __name__ == '__main__':
    main()
import paho.mqtt.client as mqtt

MQTT_ADDRESS = '192.168.1.3'  # IP Raspberry Pi của bạn
MQTT_USER = 'pi101'           # user đã tạo trong Mosquitto
MQTT_PASSWORD = '1234'        # mật khẩu tương ứng
MQTT_TOPIC_TEMP = 'temperature'  # đổi thành chữ thường
MQTT_TOPIC_HUMD = 'humidity'      # đổi thành chữ thường

def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC_TEMP)
    client.subscribe(MQTT_TOPIC_HUMD)

def on_message(client, userdata, msg):
    print(msg.topic + ' ' + msg.payload.decode('utf-8'))

def main():
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()

if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
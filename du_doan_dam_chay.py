import paho.mqtt.client as mqtt
import pandas as pd
import json
import time
import os
from sklearn.ensemble import IsolationForest
import joblib

# ===== MQTT CONFIG =====
BROKER = "pi101.local"  # hoặc "192.168.1.3"
PORT = 1883

SENSOR_TOPICS = [
    "home/bedroom/node1/temperature_sensor/value",
    "home/bedroom/node1/humidity_sensor/value",
    "home/bedroom/node1/gas_sensor/analog_value"
]

ALERT_TOPIC = "home/bedroom/node1/anomaly_alert"

CSV_FILE = "sensor_log.csv"
MODEL_FILE = "if_model.pkl"

sensor_buffer = {}

# ===== MQTT CALLBACK =====
def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8").strip()
    ts = int(time.time())
    topic_parts = msg.topic.split('/')

    if len(topic_parts) < 5:
        return

    device = topic_parts[3]
    attribute = topic_parts[4]

    try:
        if device == "temperature_sensor" and attribute == "value":
            key, val = "temperature", float(payload)
        elif device == "humidity_sensor" and attribute == "value":
            key, val = "humidity", float(payload)
        elif device == "gas_sensor" and attribute == "analog_value":
            key, val = "gas_analog", int(payload)
        else:
            return
    except ValueError:
        return

    if ts not in sensor_buffer:
        sensor_buffer[ts] = {}
    sensor_buffer[ts][key] = val

# ===== SAVE DATA =====
def save_to_csv():
    rows, ts_to_delete = [], []

    for ts, values in sensor_buffer.items():
        if all(k in values for k in ["temperature", "humidity", "gas_analog"]):
            rows.append({"timestamp": ts, **values})
            ts_to_delete.append(ts)

    if rows:
        df_new = pd.DataFrame(rows)
        if os.path.exists(CSV_FILE):
            df_old = pd.read_csv(CSV_FILE)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(CSV_FILE, index=False)

    for ts in ts_to_delete:
        sensor_buffer.pop(ts, None)

# ===== PREPROCESS =====
def preprocess_for_ml(df):
    return df.fillna(-1)

# ===== TRAIN MODEL =====
def train_model():
    df = pd.read_csv(CSV_FILE)
    df_ml = preprocess_for_ml(df.drop("timestamp", axis=1))
    model = IsolationForest(
        contamination=0.05,    
        random_state=42
    )
    model.fit(df_ml)
    joblib.dump(model, MODEL_FILE)
    print(f"✅ Model trained with {len(df)} samples.")
    return model

def load_model():
    return joblib.load(MODEL_FILE) if os.path.exists(MODEL_FILE) else None

# ===== DETECT =====
def anomaly_detect(model, row):
    df = pd.DataFrame([row.drop("timestamp")])
    df = preprocess_for_ml(df)
    if df.isnull().any().any():
        return False
    pred = model.predict(df)
    return pred[0] == -1

# ===== MAIN =====
def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    for topic in SENSOR_TOPICS:
        client.subscribe(topic)

    client.loop_start()
    model = load_model()

    while True:
        time.sleep(1)  # tốc độ xử lý ngang ESP32 gửi
        save_to_csv()

        # Train model khi có đủ dữ liệu
        if model is None and os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if len(df) >= 200:
                model = train_model()

        # Real-time anomaly check
        if model and os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if not df.empty:
                latest_row = df.iloc[-1]
                if anomaly_detect(model, latest_row):
                    alert_msg = {
                        "timestamp": int(time.time()),
                        "alert": "ANOMALY_DETECTED",
                        "values": latest_row.to_dict()
                    }
                    client.publish(ALERT_TOPIC, json.dumps(alert_msg))
                    print("⚠ anomaly:", alert_msg)

if __name__ == "__main__":
    main()

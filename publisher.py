import paho.mqtt.client as mqtt
import pandas as pd
import json
import time

# Load data from CSV (adjust delimiter and columns as needed)
df = pd.read_csv("sensor_data.csv")
# Assume there's a column 'timestamp' in ISO format or epoch, and 'sensor_id', etc.

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
DEVICE_ID = "<Your Device ID here>"  # same as IOTHUB_DEVICE_ID
TOPIC = f"devices/{DEVICE_ID}/messages/events/"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

for _, row in df.iterrows():
    # Convert row to JSON string
    data = row.to_dict()
    # If timestamp needs formatting:
    # data['timestamp'] = pd.to_datetime(data['timestamp']).isoformat()
    payload = json.dumps(data)
    result = client.publish(TOPIC, payload)
    result.wait_for_publish()
    time.sleep(0.0) 

print("Publishing complete!")
client.disconnect()

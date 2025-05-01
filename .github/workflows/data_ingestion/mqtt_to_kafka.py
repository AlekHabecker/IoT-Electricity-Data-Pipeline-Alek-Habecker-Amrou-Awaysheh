import paho.mqtt.client as mqtt
from kafka import KafkaProducer
import json
import time

# MQTT settings
MQTT_BROKER = "localhost"  # or the container name in Docker
MQTT_PORT = 1883
MQTT_TOPIC = "iot/energy"

# Kafka settings
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "energy_data"

# Kafka producer (JSON serializer)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        print(f"📡 Received MQTT: {data}")
        producer.send(KAFKA_TOPIC, value=data)
        print(f"➡️ Sent to Kafka: {KAFKA_TOPIC}")
    except Exception as e:
        print(f"⚠️ Error processing message: {e}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔄 Connecting to MQTT at {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("🛑 Exiting")
        client.disconnect()
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()

import dotenv
import os
import paho.mqtt.client as mqtt
import time

# MQTT Broker settings

dotenv.load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Create MQTT client and connect to broker

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Publish data to MQTT topic in a loop

while True:
    data = "Hello from Edge Node!"
    client.publish(MQTT_TOPIC, data)
    print(f"Published: {data}")
    time.sleep(5)
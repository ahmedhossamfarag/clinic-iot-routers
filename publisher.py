import dotenv
import os
import paho.mqtt.client as mqtt

# MQTT Broker settings

dotenv.load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Create MQTT client and connect to broker

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def connect():
    print("☁️ Connecting to MQTT Broker ...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # IMPORTANT: loop_start() tells the MQTT library to create its OWN background 
    # thread to manage network traffic. This means we don't have to manually check 
    # for network drops in our main code!
    mqtt_client.loop_start()
    print("✅ Connected to MQTT Broker!")


# Function to publish data to MQTT topic
def publish(payload):
    mqtt_client.publish(MQTT_TOPIC, payload)
    print(f"📤 Published to MQTT: {payload}")


# Function to stop the MQTT client loop and disconnect
def stop():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("🔌 Disconnected from MQTT Broker!")
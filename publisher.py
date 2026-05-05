import dotenv
import os
import paho.mqtt.client as mqtt
import ssl

# MQTT Broker settings

dotenv.load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_STATE_TOPIC = os.getenv("MQTT_STATE_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
TLS_CA_FILE = os.getenv("TLS_CA_FILE")
TLS_CERT_FILE = os.getenv("TLS_CERT_FILE")
TLS_KEY_FILE = os.getenv("TLS_KEY_FILE")

# Create MQTT client and connect to broker

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

if TLS_CA_FILE:
    base_path = os.path.dirname(__file__)
    mqtt_client.tls_set(
        ca_certs=os.path.join(base_path, TLS_CA_FILE),
        certfile=os.path.join(base_path, TLS_CERT_FILE) if TLS_CERT_FILE else None,
        keyfile=os.path.join(base_path, TLS_KEY_FILE) if TLS_KEY_FILE else None,
        tls_version=ssl.PROTOCOL_TLSv1_2
        )

def connect():
    print("☁️ Connecting to MQTT Broker ...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # IMPORTANT: loop_start() tells the MQTT library to create its OWN background 
    # thread to manage network traffic. This means we don't have to manually check 
    # for network drops in our main code!
    mqtt_client.on_connect = on_connect
    mqtt_client.on_connect_fail = on_connect_fail
    mqtt_client.loop_start()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
    else:
        print(f"❌ Connection failed with code {rc}")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        os._exit(1)


def on_connect_fail(client, userdata, rc):
    print(f"❌ Connection failed with code {rc}")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    os._exit(1)


# Function to publish data to MQTT topic
def publish(payload):
    mqtt_client.publish(MQTT_TOPIC, payload)
    print(f"📤 Published to MQTT: {payload}")


def publish_state(payload):
    mqtt_client.publish(MQTT_STATE_TOPIC, payload)
    print(f"📤 Published state to MQTT: {payload}")


# Function to stop the MQTT client loop and disconnect
def stop():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("🔌 Disconnected from MQTT Broker!")
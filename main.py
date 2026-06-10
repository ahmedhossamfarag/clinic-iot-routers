import dotenv  # Loads environment variables from a .env file (for MQTT credentials)
import os  # Accesses those environment variables
import asyncio  # Handles asynchronous tasks (waiting for BLE without freezing)
from bleak import BleakScanner  # The core Bluetooth Low Energy library
import time  # Added to fix the CPU max-out bug in the main loop
import publisher as mqtt_client  # Our custom MQTT publishing module (see publisher.py)
import utils  # Our custom utility functions (see utils.py)

# ==============================================================================
# BLE SETTINGS
# ==============================================================================
dotenv.load_dotenv()

DEVICE_NAME = os.getenv("DEVICE_NAME")
SERVICE_ID = os.getenv("SERVICE_ID")
MIN_RSSI = int(os.getenv("MIN_RSSI", -80))  # Default to -80 if not set
MIN_PUBLISH_INTERVAL = int(os.getenv("MIN_PUBLISH_INTERVAL", 10))  # Default to 10
DEFAULT_RSSI = -9999
ROUTER_ACTIVE_INTERVAL = int(
    os.getenv("ROUTER_ACTIVE_INTERVAL", 60)
)  # Default to 60 seconds

# This should be replaced with code that retrieves the actual MAC address of the ESP32 when deployed on hardware. For testing on a computer, you can set it to any unique identifier.
ROUTER_ID = os.getenv("ROUTER_ID")  # The mac address of the current router. Should be replaced with the actual mac address when ESP32 is used.

# ==============================================================================
# GLOBAL ASYNC QUEUE and DICT
# ==============================================================================
publish_queue = asyncio.Queue(maxsize=1000)
last_sent = dict()
max_rssi = dict()

# ==============================================================================
# BLE ADVERTISEMENT HANDLER
# ==============================================================================


def advertisement_handler(device, advertisement_data):
    if device.name != DEVICE_NAME:
        return

    if advertisement_data.rssi < MIN_RSSI:
        return


    # Extract the service UUIDs from the advertisement data
    service_uuids = advertisement_data.service_uuids

    if not service_uuids:
        return

    if SERVICE_ID not in service_uuids[0]:
        return

    print(f"📡 Detected BLE Advertisement from {device.name} ({device.address.lower()})")

    try:
        publish_queue.put_nowait((device.address.lower(), advertisement_data.rssi))
    except Exception:
        print("⚠️ Publish queue full. Skipping...")
        pass


# ==============================================================================
# ASYNC BLE LOOP (The Background Engine)
# ==============================================================================
async def ble_scanner_task():
    scanner = BleakScanner(detection_callback=advertisement_handler)

    # Turn on the computer's Bluetooth receiver
    await scanner.start()
    print("📶 BLE scanner started.")

    try:
        # Keep the background scanning task alive indefinitely.
        while True:
            await asyncio.sleep(1)  # Sleep briefly to prevent maxing out the CPU
    finally:
        # If the script closes, turn off the scanner cleanly.
        await scanner.stop()
        print("🛑 BLE scanner stopped.")


# ==============================================================================
# QUEUE CONSUMER -> MQTT
# ==============================================================================


def can_publish(device_id):
    now = time.time()
    if device_id in last_sent:
        if now - last_sent[device_id] < MIN_PUBLISH_INTERVAL:
            return False

    return True


def mark_published(device_id):
    last_sent[device_id] = time.time()


def getRSSI(device_id, rssi):
    return max(max_rssi.get(device_id, DEFAULT_RSSI), rssi)


def setRSSI(device_id, rssi):
    max_rssi[device_id] = getRSSI(device_id, rssi)


def resetRSSI(device_id):
    max_rssi.pop(device_id, None)


async def mqtt_publisher_task():
    while True:
        data = await publish_queue.get()

        # Check last sent time
        if not can_publish(data[0]):
            setRSSI(data[0], data[1])
            publish_queue.task_done()
            continue

        # Convert the raw bytes into a Python dictionary
        rssi = getRSSI(data[0], data[1])
        data_dict = utils.json_serializable(ROUTER_ID, data[0], rssi)

        if data_dict:
            try:
                mqtt_client.publish(data_dict)
                mark_published(data[0])
                resetRSSI(data[0])
            except Exception:
                setRSSI(data[0], data[1])
                pass

        publish_queue.task_done()


# ==============================================================================
# MQTT RECONNECT HANDLER
# ==============================================================================
async def mqtt_reconnect_task():
    print("🔄 MQTT reconnect monitor started.")

    while True:
        try:
            # If your publisher.py has is_connected(), use it here
            if not mqtt_client.is_connected():
                print("🔌 MQTT disconnected. Reconnecting...")
                mqtt_client.connect()

        except AttributeError:
            pass

        except Exception as e:
            print(f"⚠️ Reconnect error: {e}")

        await asyncio.sleep(5)


# ==============================================================================
# MQTT Router Active signal (Optional, can be used for debugging or future features)
# ==============================================================================
async def mqtt_router_active_task():
    print("🔄 MQTT router active signal started.")

    while True:
        try:
            payload = utils.json_serializable_active_signal(ROUTER_ID)
            if payload:
                mqtt_client.publish_active_signal(payload)
        except Exception as e:
            pass

        await asyncio.sleep(ROUTER_ACTIVE_INTERVAL)


# ==============================================================================
# THREAD HELPER
# ==============================================================================
async def main():
    print("⚡ Starting system...")

    # Initial MQTT connection
    mqtt_client.connect()

    while not mqtt_client.mqtt_client.is_connected():
        print("⏳ Waiting for MQTT connection...")
        await asyncio.sleep(1)

    await asyncio.gather(
        ble_scanner_task(),
        mqtt_publisher_task(),
        mqtt_reconnect_task(),
        mqtt_router_active_task(),
    )


# ==============================================================================
# SCRIPT ENTRY POINT (The Main Thread)
# ==============================================================================
if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n🛑 Script manually stopped by user.")

    finally:
        mqtt_client.stop()
        print("🔌 Disconnected from MQTT Server. Exiting...")

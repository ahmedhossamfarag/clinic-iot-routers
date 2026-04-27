import dotenv                 # Loads environment variables from a .env file (for MQTT credentials)
import os                    # Accesses those environment variables
import asyncio               # Handles asynchronous tasks (waiting for BLE without freezing)
from bleak import BleakScanner # The core Bluetooth Low Energy library
import time                  # Added to fix the CPU max-out bug in the main loop
import publisher as mqtt_client            # Our custom MQTT publishing module (see publisher.py)
import utils                 # Our custom utility functions (see utils.py)
# ============================================================================== 
# BLE SETTINGS
# ==============================================================================
dotenv.load_dotenv()

DEVICE_NAME = os.getenv("DEVICE_NAME")
ROUTER_ID = os.getenv("ROUTER_ID")
MIN_RSSI = int(os.getenv("MIN_RSSI", -80))  # Default to -80 if not set
MIN_PUBLISH_INTERVAL = int(os.getenv("MIN_PUBLISH_INTERVAL", 10))  # Default to 10

# ==============================================================================
# GLOBAL ASYNC QUEUE and DICT
# ==============================================================================
publish_queue = asyncio.Queue()
last_sent = dict()

# ============================================================================== 
# BLE ADVERTISEMENT HANDLER
# ==============================================================================

def advertisement_handler(device, advertisement_data):
    if device.name != DEVICE_NAME:
        return

    if advertisement_data.rssi < MIN_RSSI:
        return

    print(f"📡 Detected BLE Advertisement from {device.name} ({device.address})")

    # Extract the service UUIDs from the advertisement data
    service_uuids = advertisement_data.service_uuids

    if not service_uuids:
        return

    try:
        publish_queue.put_nowait((service_uuids[0], advertisement_data.rssi))
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

def will_publish(device_id):
    now = time.time()
    if device_id in last_sent:
        if now - last_sent[device_id] < MIN_PUBLISH_INTERVAL:
            return False
    
    last_sent[device_id] = now
    return True

async def mqtt_publisher_task():
    while True:
        data = await publish_queue.get()

        # Check last sent time
        if not will_publish(data[0]):
            continue
        
        # Convert the raw bytes into a Python dictionary
        data_dict = utils.json_serializable(ROUTER_ID, data[0], data[1])

        if data_dict:
            try:
                mqtt_client.publish(data_dict)
            except Exception:
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
        mqtt_reconnect_task()    
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


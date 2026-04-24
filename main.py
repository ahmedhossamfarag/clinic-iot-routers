import dotenv                 # Loads environment variables from a .env file (for MQTT credentials)
import os                    # Accesses those environment variables
import asyncio               # Handles asynchronous tasks (waiting for BLE without freezing)
from bleak import BleakScanner # The core Bluetooth Low Energy library
import threading             # Allows us to run multiple "lanes" of code simultaneously
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
# MQTT CONNECTION
# ==============================================================================
mqtt_client.connect()


# ============================================================================== 
# BLE ADVERTISEMENT HANDLER
# ==============================================================================
last_sent = dict()

def will_publish(device_id):
    now = time.time()
    if device_id in last_sent:
        if now - last_sent[device_id] < MIN_PUBLISH_INTERVAL:
            return False
    
    last_sent[device_id] = now
    return True


def advertisement_handler(device, advertisement_data):
    if DEVICE_NAME == device.name and advertisement_data.rssi >= MIN_RSSI:
        print(f"📡 Detected BLE Advertisement from {device.name} ({device.address})")

        # Extract the service UUIDs from the advertisement data
        service_uuids = advertisement_data.service_uuids

        if service_uuids and len(service_uuids):
            # Check last sent time
            if not will_publish(service_uuids[0]):
                return
            
            # Convert the raw bytes into a Python dictionary
            data_dict = utils.json_serializable(ROUTER_ID, service_uuids[0], advertisement_data.rssi)

            if data_dict:
                mqtt_client.publish(data_dict)
            else:
                print("⚠️ Data is not JSON serializable. Skipping publish.")
            

# ============================================================================== 
# ASYNC BLE LOOP (The Background Engine)
# ==============================================================================
async def run_ble_scanner():
    scanner = BleakScanner(detection_callback=advertisement_handler)
    
    # Turn on the computer's Bluetooth receiver
    await scanner.start()
    
    try:
        # Keep the background scanning task alive indefinitely.
        while True:
            await asyncio.sleep(1)  # Sleep briefly to prevent maxing out the CPU
    finally:
        # If the script closes, turn off the scanner cleanly.
        await scanner.stop()

# ============================================================================== 
# THREAD HELPER
# ==============================================================================
def start_ble_in_thread():
    # Create a new asyncio event loop for this thread, since the main thread is busy with MQTT.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Execute our 'run_ble_scanner' function inside this new loop
    loop.run_until_complete(run_ble_scanner())

# ============================================================================== 
# SCRIPT ENTRY POINT (The Main Thread)
# ==============================================================================
if __name__ == "__main__":
    
    # 1. CREATE THE BACKGROUND THREAD
    # daemon=True means "If the main script closes, immediately kill this thread too." 
    # Otherwise, the script would keep running invisibly in the background.
    ble_thread = threading.Thread(target=start_ble_in_thread, daemon=True)
    ble_thread.start()
    
    try:
        print("⚡ Main thread running MQTT. BLE is running in background thread.")
        
        # 2. THE MAIN LOOP
        # We need an infinite loop here to keep the main Python script from reaching 
        # the end of the file and closing immediately.
        while True:
            # Sleep briefly to prevent maxing out the CPU. 
            # The BLE scanning is happening in the background thread, so we don't need to do anything here.
            time.sleep(1)
            
    except KeyboardInterrupt:
        # 3. CLEAN SHUTDOWN
        # If you press Ctrl+C, catch the error and execute a graceful shutdown sequence.
        print("\n🛑 Script manually stopped by user.")
        
        # Stop the background network agent
        mqtt_client.stop()
        
        print("🔌 Disconnected from MQTT Server. Exiting...")
import dotenv                 # Loads environment variables from a .env file (for MQTT credentials)
import time                  # Added to fix the CPU max-out bug in the main loop
import publisher as mqtt_client            # Our custom MQTT publishing module (see publisher.py)
import utils                 # Our custom utility functions (see utils.py)
import random

dotenv.load_dotenv()

# -----------------------------------
# IDs
# -----------------------------------
ROUTER_1_ID = 'b39a573f-bb53-43e9-9c1b-1cf500a040f3'
ROUTER_2_ID = '77e830e1-ab7e-4de5-9c85-c3a2422c8f83'

DEVICE_1_ID = 'a38deac2-1ab2-4d23-8ba4-e68399782297'
DEVICE_2_ID = '942a4d7a-1b54-4b20-9d26-726a018e6caa'


# -----------------------------------
# Existing publisher
# -----------------------------------
def publish_msg(router_id, device_id, rssi):
    data = utils.json_serializable(router_id, device_id, rssi)

    try:
        mqtt_client.publish(data)
    except Exception:
        pass


# -----------------------------------
# Helper
# -----------------------------------
def wait(sec=1):
    time.sleep(sec)


# -----------------------------------
# TEST 1
# New devices -> insert records
# -----------------------------------
def test_initial_insert():
    print("TEST 1: Initial insert")

    publish_msg(ROUTER_1_ID, DEVICE_1_ID, -62)
    wait()

    publish_msg(ROUTER_2_ID, DEVICE_2_ID, -53)
    wait()


# -----------------------------------
# TEST 2
# Duplicate same router -> update RSSI
# -----------------------------------
def test_duplicate_same_router():
    print("TEST 2: Duplicate same router")

    publish_msg(ROUTER_1_ID, DEVICE_1_ID, -61)
    wait(0.5)

    publish_msg(ROUTER_1_ID, DEVICE_1_ID, -59)
    wait()


# -----------------------------------
# TEST 3
# Duplicate different router stronger RSSI
# Should handoff
# -----------------------------------
def test_duplicate_router_handoff():
    print("TEST 3: Stronger router handoff")

    publish_msg(ROUTER_1_ID, DEVICE_2_ID, -70)
    wait(0.5)

    publish_msg(ROUTER_2_ID, DEVICE_2_ID, -55)
    wait()


# -----------------------------------
# TEST 4
# Duplicate different router weaker RSSI
# Should ignore
# -----------------------------------
def test_duplicate_weaker_router():
    print("TEST 4: Weaker router ignored")

    publish_msg(ROUTER_2_ID, DEVICE_1_ID, -50)
    wait(0.5)

    publish_msg(ROUTER_1_ID, DEVICE_1_ID, -72)
    wait()


# -----------------------------------
# TEST 5
# New signal after timeout
# Need wait > DEVICES_SIGNAL_PERIOD
# -----------------------------------
def test_new_signal_after_timeout():
    print("TEST 5: New signal after timeout")

    wait(6)   # adjust to exceed DEVICES_SIGNAL_PERIOD

    publish_msg(ROUTER_1_ID, DEVICE_1_ID, -63)
    wait()


# -----------------------------------
# TEST 6
# Consecutive same router after timeout
# Should update old record instead insert
# -----------------------------------
def test_two_consecutive_same_router():
    print("TEST 6: Two consecutive same router")

    publish_msg(ROUTER_2_ID, DEVICE_2_ID, -60)
    wait(6)

    publish_msg(ROUTER_2_ID, DEVICE_2_ID, -58)
    wait(6)

    publish_msg(ROUTER_2_ID, DEVICE_2_ID, -57)
    wait()


# -----------------------------------
# TEST 7
# Device roaming back and forth
# -----------------------------------
def test_roaming():
    print("TEST 7: Roaming simulation")

    signals = [
        (ROUTER_1_ID, -50),
        (ROUTER_1_ID, -55),
        (ROUTER_2_ID, -48),
        (ROUTER_2_ID, -46),
        (ROUTER_1_ID, -49),
        (ROUTER_2_ID, -44),
    ]

    for router, rssi in signals:
        publish_msg(router, DEVICE_1_ID, rssi)
        wait(1)


# -----------------------------------
# TEST 8
# High traffic random stress test
# -----------------------------------
def test_stress():
    print("TEST 8: Stress test")

    routers = [ROUTER_1_ID, ROUTER_2_ID]
    devices = [DEVICE_1_ID, DEVICE_2_ID]

    for _ in range(50):
        publish_msg(
            random.choice(routers),
            random.choice(devices),
            random.randint(-75, -45)
        )
        wait(0.2)


# -----------------------------------
# RUN ALL TESTS
# -----------------------------------
def run_all_tests():
    test_initial_insert()
    test_duplicate_same_router()
    test_duplicate_router_handoff()
    test_duplicate_weaker_router()
    test_new_signal_after_timeout()
    test_two_consecutive_same_router()
    test_roaming()
    test_stress()

    print("All tests completed.")


# -----------------------------------
# Execute
# -----------------------------------
mqtt_client.connect()
wait()
run_all_tests()


import json
import uuid


# Utility function to check if a string is a valid UUID
def is_uuid(value: str):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False
    

# Utility function to check if an object is JSON serializable
def json_serializable(router_id: str, device_id: str, rssi):
    try:
        obj = {
            "router_id": router_id,
            "device_id": device_id,
            "rssi": int(rssi)
        }
        data = json.dumps(obj)
        return data
    except (TypeError, OverflowError):
        return False
    

def json_serializable_state(router_id: str, device_id: str, state: int):
    try:
        obj = {
            "router_id": router_id,
            "device_id": device_id,
            "state": state
        }
        data = json.dumps(obj)
        return data
    except (TypeError, OverflowError):
        return False
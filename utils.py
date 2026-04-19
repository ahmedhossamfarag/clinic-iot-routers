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
def json_serializable(router_id: str, device_id: str):
    try:
        obj = {
            "router_id": router_id,
            "device_id": device_id
        }
        data = json.dumps(obj)
        return data
    except (TypeError, OverflowError):
        return False
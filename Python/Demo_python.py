import urllib.request
import json
import requests
TIMEOUT = 5

BASE_URL = "http://localhost:22001/NeuLogAPI"
TIMEOUT = 5


def get_sensor_value(sensor_name: str, sensor_id: int):
    """
    Fetch a single sensor reading from the NeuLog API.

    Args:
        sensor_name: The sensor type (e.g. 'Light', 'Temperature', 'Distance')
        sensor_id:   The sensor module ID (usually 1)

    Returns:
        The sensor value, or None on failure.
    """
    url = f"{BASE_URL}?GetSensorValue:[{sensor_name}],[{sensor_id}]"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        # NeuLog returns a list like [sensor_name, id, value]
        if isinstance(data, list) and len(data) >= 3:
            return float(data[2])
        return data

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to NeuLog server at {BASE_URL}. Is it running?")
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {TIMEOUT}s.")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
    except ValueError:
        print("[ERROR] Could not parse sensor value from response.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return None


def main():

    sensor_name = "Light"
    sensor_id = 1

    print("=== NeuLog Sensor Reader ===\n")
    print(f"Reading {sensor_name} sensor (ID {sensor_id})...")

    value = get_sensor_value(sensor_name, sensor_id)

    if value is not None:
        print(f"→ {sensor_name} sensor value: {value}")
    else:
        print("→ Failed to read sensor.")


if __name__ == "__main__":
    main()
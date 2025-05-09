import asyncio
import requests
import base64
import json
import random
import os
import time

API_KEY = os.environ.get("API_KEY", '')  # Replace with your ChirpStack API key
APPLICATION_ID = os.environ.get('APPLICATION_ID', 'test')

DEVICE_EUI = '0004a30b001c12ab'  # Replace with your device EUI
CHIRPSTACK_API_URL = "http://chirpstack-rest-api:8090/api/devices" #replace if needed
F_PORT = 1
SEND_INTERVAL = 1  # Seconds between uplinks
DEVICE_PROFILE_ID = "adbcc190-8fb5-43d0-88d2-93e7fdc3ed07"


async def simulate_uplink_via_mqtt(mqtt_client, sensor_data):
    """Constructs and publishes a simulated uplink message via MQTT."""

    # Encode sensor data as Base64
    payload_bytes = json.dumps(sensor_data).encode("utf-8")
    payload_b64 = base64.b64encode(payload_bytes).decode("utf-8")

    # Construct the simulated uplink payload (JSON format expected by Gateway Bridge)
    # NOTE: The exact structure might vary slightly based on your Gateway Bridge version and config!
    uplink_payload = {
        "rxInfo": {
            "gatewayID": SIMULATED_GATEWAY_ID,
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), # Current time
            "rssi": random.randint(-120, -60), # Simulated RSSI
            "loraSNR": random.uniform(-5, 15), # Simulated SNR
            "frequency": 868100000,            # Simulated Frequency (EU868 example)
            "dr": 5,                           # Simulated Data Rate (e.g., SF7BW125)
            # ... other rxInfo fields as needed by your GW Bridge config
        },
        "txInfo": {
            "frequency": 868100000,
            "dr": 5,
            # ... other txInfo fields
        },
        "phyPayload": payload_b64, # The Base64 encoded LoRaWAN payload
        # Note: Some Gateway Bridge versions might expect fields like "devEUI", "fCnt", "fPort"
        # directly in the top level or within a specific structure.
        # Check your Gateway Bridge documentation/config!
        "devEUI": DEVICE_EUI, # Often included for convenience, though technically part of phyPayload
        "fCnt": random.randint(0, 65535), # Simulated Frame Counter
        "fPort": F_PORT,
        # ... other fields like "confirmed" if simulating confirmed uplinks
    }

    try:
        # Publish the JSON payload to the Gateway Bridge's uplink topic
        mqtt_client.publish(GATEWAY_BRIDGE_UPLINK_TOPIC, json.dumps(uplink_payload))
        print(f"Simulated uplink sent for {DEVICE_EUI} via MQTT to {GATEWAY_BRIDGE_UPLINK_TOPIC}")
        print(f"Payload: {uplink_payload}")
    except Exception as e:
        print(f"Error publishing simulated uplink via MQTT: {e}")


async def generate_sensor_data():
    """Generates random sensor data."""
    temperature = random.uniform(20, 30)
    humidity = random.uniform(40, 60)
    return {"temperature": temperature, "humidity": humidity}

async def send_uplink(data):
    """Sends an uplink message to ChirpStack."""
    payload_bytes = json.dumps(data).encode("utf-8")
    payload_b64 = base64.b64encode(payload_bytes).decode("utf-8")

    url = f"{CHIRPSTACK_API_URL}/{DEVICE_EUI}/queue"
    headers = {
        "Grpc-Metadata-Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    message = {
        "devEUI": DEVICE_EUI,
        "fPort": F_PORT,
        "data": payload_b64,
    }

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, headers=headers, json=message)
        )
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        print(f"Uplink sent successfully: {data}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending uplink: {e}")

def register_device():
    """Registers a device in ChirpStack using the API."""

    headers = {
        "Grpc-Metadata-Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "device": {
            "applicationID": APPLICATION_ID,
            "description": "Simulated Device",
            "devEUI": DEVICE_EUI,
            "deviceProfileID": DEVICE_PROFILE_ID,
            "isDisabled": False,
            "name": 'Simulated Device',
            "skipFCntCheck": False,
            "tags": [],
            "variables": {}
        }
    }

    try:
        response = requests.post(CHIRPSTACK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Device {DEVICE_EUI} registered successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error registering device: {e}")

async def simulate_device():
    """Simulates a LoRaWAN device sending uplinks."""
    register_device()
    while True:
        sensor_data = await generate_sensor_data()
        await send_uplink(sensor_data)
        await asyncio.sleep(SEND_INTERVAL)

async def main():
    await simulate_device()

if __name__ == "__main__":
    asyncio.run(main())
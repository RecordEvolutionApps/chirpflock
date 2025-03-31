import asyncio
import requests
import base64
import json
import random
import os

API_KEY = os.environ.get("API_KEY", '')  # Replace with your ChirpStack API key
APPLICATION_ID = os.environ.get('APPLICATION_ID', '')

DEVICE_EUI = '0004A30B001C12AB'  # Replace with your device EUI
CHIRPSTACK_API_URL = "http://chirpstack-rest-api:8090/api/devices" #replace if needed
F_PORT = 1
SEND_INTERVAL = 1  # Seconds between uplinks
DEVICE_PROFILE_ID = "EU868"

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
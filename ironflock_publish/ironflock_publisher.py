import asyncio
import json
import base64
import struct
import os
from ironflock import IronFlock
import paho.mqtt.client as mqtt

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
APPLICATION_ID = os.environ.get('APPLICATION_ID', '')

def on_connect(client, userdata, flags, rc, properties):
    print(f"Connected with result code {rc}")
    # Subscribe to the uplink topic
    client.subscribe(f"application/{APPLICATION_ID}/device/+/event/up")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        uplink_data = data["uplinkEvent"]
        payload = transform_payload(uplink_data) #your transform payload function.
        ironflock.publish_to_table('sensordata', [payload])

    except Exception as e:
        print(f"Error processing message: {e}")

async def transform_payload(data):
    """Processes uplink data from ChirpStack and transforms the payload."""
    print("received raw data", data)
    try:
        
        transformed_data = {
            "publishedAt": data.get("publishedAt"),
            "devEUI": data.get("devEUI"),
            "fPort": data.get("fPort"),
            "data": base64.b64decode(data.get("data", "")).decode("utf-8") if data.get("data") else None, #decode base64
            "dr": data.get("dr"),
            "adr": data.get("adr"),
            "fCnt": data.get("fCnt"),
            "rssi": data.get("rxInfo", [{}])[0].get("rssi"),
            "snr": data.get("rxInfo", [{}])[0].get("snr"),
            "confirmedUplink": data.get("confirmedUplink"),
            "object": json.dumps(data.get("object")) if data.get("object") else None, #convert object to json string.
        }

        print("transformed data", transformed_data)
        return transformed_data

    except Exception as e:
        print(f"Error processing uplink: {e}")
        print(f"Raw data: {data}")

async def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.loop_start()

if __name__ == "__main__":
    ironflock = IronFlock(mainFunc=main)
    ironflock.run()
import asyncio
import json
import base64
import struct
import os
import sys
# Assuming IronFlock is a library that manages an asyncio event loop
# and provides a run() method that starts it.
# Replace with the actual import if IronFlock is structured differently.
from ironflock import IronFlock


import paho.mqtt.client as mqtt

import logging
# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Read configuration from environment variables
MQTT_BROKER = os.environ.get("MQTT_BROKER_HOST", "mosquitto") # Default to service name
MQTT_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883)) # Default to standard port
APPLICATION_ID = os.environ.get('APPLICATION_ID', '') # Keep default empty if not set
ENABLE_DEMO_DATA = (os.environ.get('ENABLE_DEMO_DATA', 'false').lower() == 'true') # Case-insensitive check

# --- Global IronFlock Instance ---
# This will be initialized in __main__
ironflock_instance = None

# --- MQTT Callbacks ---

def on_connect(client, userdata, flags, rc, properties):
    """Called when the MQTT client connects to the broker."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to the uplink topic
        # Use the configured APPLICATION_ID if set, otherwise subscribe to all
        subscribe_topic = f"application/{APPLICATION_ID}/device/+/event/up" if APPLICATION_ID else "application/+/device/+/event/up"
        client.subscribe(subscribe_topic)
        logger.info(f"Subscribed to MQTT topic: {subscribe_topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")
        # Implement reconnection logic or error handling if needed

def on_message(client, userdata, msg):
    """Called when an MQTT message is received."""
    logger.info(f"Received MQTT message on topic: {msg.topic}")
    try:
        # Decode payload from bytes to string, then parse JSON
        data = json.loads(msg.payload.decode("utf-8"))
        logger.info(f"Parsed MQTT payload data: %s", data)

        # Extract application ID from the topic string
        topic_parts = msg.topic.split('/')
        application_id_from_topic = None
        # Expected format: "application/<ApplicationID>/device/<DevEUI>/event/up"
        if len(topic_parts) > 1 and topic_parts[0] == "application":
            application_id_from_topic = topic_parts[1]
            # logger.debug(f"Extracted Application ID: {application_id_from_topic}")
        else:
            logger.warning(f"Could not extract Application ID from topic: {msg.topic}")

        # Transform the raw payload
        # Pass the extracted application_id, not the global one if topic extraction is preferred
        payload = transform_payload(data, application_id_from_topic)

        # --- Schedule WAMP Publish using call_soon_threadsafe ---
        # We are in the MQTT client's thread (due to loop_start).
        # We need to schedule the async WAMP publish task to run in the main asyncio event loop.
        # Get the running event loop (assuming IronFlock.run() starts and manages it)
        loop = asyncio.get_event_loop()

        # Schedule the coroutine to run in the event loop
        # Use a lambda or partial to pass arguments to the async function
        loop.call_soon_threadsafe(
            asyncio.create_task, # The function to call in the loop's thread
            ironflock_instance.publish_to_table('sensordata', [payload]) # The coroutine to schedule
        )
        logger.info("Scheduled publish to IronFlock table 'sensordata'")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON payload from MQTT.")
        logger.error(msg.payload)
    except Exception as e:
        logger.error(f"An error occurred processing message: {e}", exc_info=True)


def on_disconnect(client, userdata, rc):
    """Called when the MQTT client disconnects from the broker."""
    if rc != 0:
        logger.warning(f"MQTT client disconnected unexpectedly with return code {rc}")
        # loop_start() will attempt to reconnect automatically.
        # You could add custom logging or actions here.
    else:
        logger.info("MQTT client disconnected gracefully.")


# --- Payload Transformation ---

def transform_payload(data, application_id):
    """
    Processes uplink data from ChirpStack and transforms the payload
    into a format suitable for IronFlock.
    """
    # logger.info("Received raw data for transformation: %s", data) # Use logger.info for structured data

    try:
        transformed_data = {
            "tsp": data.get("publishedAt"),
            "applicationId": application_id,
            "devEUI": data.get("devEUI"),
            "fPort": data.get("fPort"),
            "data": base64.b64decode(data.get("data", "")).decode("utf-8") if data.get("data") else None,  # Decode Base64
            "dr": data.get("txInfo", {}).get("dr"),
            "adr": data.get("adr"),
            "fCnt": data.get("fCnt"),
            "rssi": data.get("rxInfo", [{}])[0].get("rssi"),
            "snr": data.get("rxInfo", [{}])[0].get("snr"),
            "confirmedUplink": data.get("confirmedUplink"),
            "object": json.dumps(data.get("object")) if data.get("object") else None,  # Convert object to JSON string
        }

        logger.info("Transformed data: %s", transformed_data) # Use logger.info for structured data
        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming uplink payload: {e}", exc_info=True)
        logger.error(f"Raw data that caused error: %s", data)
        # Depending on requirements, you might return None or raise the exception
        return None

# --- Main Execution ---

async def main_async():
    """Main asynchronous function for the application logic."""
    logger.info("Starting IronFlock Publisher application...")

    # MQTT Client Setup
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect # Assign disconnect handler

    # If authentication is needed for Mosquitto
    # MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
    # MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
    # if MQTT_USERNAME and MQTT_PASSWORD:
    #     client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    #     logger.info("MQTT authentication enabled.")

    try:
        # Connect to MQTT broker - this is a blocking call in this context (loop_start)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Attempting to connect to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except ConnectionRefusedError:
        logger.error(f"MQTT Connection refused. Make sure the Mosquitto broker is running and accessible at {MQTT_BROKER}:{MQTT_PORT}")
        sys.exit(1) # Exit if initial connection fails
    except Exception as e:
        logger.error(f"An error occurred during initial MQTT connection: {e}", exc_info=True)
        sys.exit(1) # Exit on other connection errors

    # Start the MQTT network loop in a separate thread.
    # This allows the main thread to run the asyncio event loop.
    client.loop_start()
    logger.info("MQTT client loop started in a separate thread.")

    # The main asyncio loop is managed by IronFlock.run().
    # Your main_async function should contain any other tasks you need running
    # in the main asyncio loop besides the MQTT message processing scheduled
    # from the on_message callback.
    # For this script, the primary logic is in the on_message callback,
    # scheduled via call_soon_threadsafe.
    # So, main_async just needs to keep running.

    # Keep the main_async function running indefinitely
    # This prevents the asyncio loop from stopping immediately after loop_start()
    # You could add other asyncio tasks here if needed.
    while True:
        await asyncio.sleep(3600) # Sleep for a long time, or indefinitely


if __name__ == "__main__":
    # Initialize the IronFlock instance
    ironflock_instance = IronFlock(mainFunc=main_async)

    # Run the application using IronFlock's run method
    # This is expected to start and manage the asyncio event loop
    logger.info("Starting application using IronFlock.run()...")
    try:
        ironflock_instance.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during IronFlock execution: {e}", exc_info=True)
        sys.exit(1)


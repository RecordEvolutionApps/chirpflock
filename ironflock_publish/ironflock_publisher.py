import asyncio
import json
import logging
import os
import sys
from datetime import datetime

import paho.mqtt.client as mqtt

# Assuming IronFlock is a library that manages an asyncio event loop
# and provides a run() method that starts it.
# Replace with the actual import if IronFlock is structured differently.
from ironflock import IronFlock

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Read configuration from environment variables.
# DEVICE_KEY is injected by the IronFlock platform at runtime. Read it lazily so
# the module can be imported (and a clear error logged) even when it is unset,
# instead of crashing with a bare KeyError at import time.
DEVICE_KEY = os.environ.get("DEVICE_KEY")
MQTT_BROKER = os.environ.get("MQTT_BROKER_HOST", "mosquitto")  # Default to service name
MQTT_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883))  # Default to standard port
APPLICATION_ID = os.environ.get("APPLICATION_ID", "")  # Keep default empty if not set

# --- Global IronFlock Instance ---
# This will be initialized in __main__
ironflock_instance = None
main_asyncio_loop = None  # Global variable to store the main event loop reference

# --- MQTT Callbacks ---


def on_connect(client, userdata, flags, rc, properties):
    """Called when the MQTT client connects to the broker."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to the uplink topic
        # Use the configured APPLICATION_ID if set, otherwise subscribe to all
        subscribe_topic = (
            f"application/{APPLICATION_ID}/device/+/event/up"
            if APPLICATION_ID
            else "application/+/device/+/event/up"
        )
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
        logger.info("Parsed MQTT payload data: %s", data)

        # Transform the raw payload
        # Pass the extracted application_id, not the global one if topic extraction is preferred
        payload = transform_payload(data)

        # --- Schedule WAMP Publish on the main asyncio loop ---
        # We are in the MQTT client's thread (paho's loop_start). publish_to_table
        # is a coroutine that must run on the asyncio loop in the main thread.
        # asyncio.run_coroutine_threadsafe is the documented way to hand a coroutine
        # to a loop from another thread: it schedules the task ON the loop, keeps a
        # strong reference so it can't be garbage-collected mid-flight (a bare
        # call_soon_threadsafe(create_task, ...) does not), and returns a
        # concurrent.futures.Future we can use to surface any publish error.
        if payload is None:
            logger.warning("transform_payload returned None; skipping publish.")
        elif main_asyncio_loop is not None:
            future = asyncio.run_coroutine_threadsafe(
                ironflock_instance.publish_to_table("sensordata", payload),
                main_asyncio_loop,
            )

            def _log_publish_result(fut):
                try:
                    fut.result()
                except Exception:
                    logger.error(
                        "Publish to IronFlock table 'sensordata' failed.", exc_info=True
                    )

            future.add_done_callback(_log_publish_result)
            logger.info("Scheduled publish to IronFlock table 'sensordata'")
        else:
            logger.error(
                "Main asyncio loop not available. Cannot schedule WAMP publish."
            )

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


def transform_payload(data):
    """
    Processes uplink data from ChirpStack and transforms the payload
    into a format suitable for IronFlock.
    """
    # logger.info("Received raw data for transformation: %s", data) # Use logger.info for structured data

    try:
        # Default to an empty dict so a missing "deviceInfo" key yields None
        # fields instead of raising AttributeError.
        device_info = data.get("deviceInfo") or {}
        transformed_data = {
            "time": data.get("time"),
            "tenantId": device_info.get("tenantId"),
            "tenantName": device_info.get("tenantName"),
            "applicationId": device_info.get("applicationId"),
            "applicationName": device_info.get("applicationName"),
            "deviceProfileId": device_info.get("deviceProfileId"),
            "deviceProfileName": device_info.get("deviceProfileName"),
            "devEUI": device_info.get("devEui"),
            "deviceName": device_info.get("deviceName"),
            "rawData": data.get("data"),
            "object": data.get("object"),
        }

        logger.info(
            "Transformed data: %s", transformed_data
        )  # Use logger.info for structured data
        return transformed_data

    except Exception as e:
        logger.error(f"Error transforming uplink payload: {e}", exc_info=True)
        logger.error("Raw data that caused error: %s", data)
        # Depending on requirements, you might return None or raise the exception
        return None


async def register_device():
    print("########### Storing Device info ################")
    await ironflock_instance.publish_to_table(
        "devices",
        {
            "tsp": datetime.now().astimezone().isoformat(),
            "url": f"https://{DEVICE_KEY}-chirpflock-47836.app.ironflock.com",
            "deleted": False,
        },
    )
    print("done")


# --- Main Execution ---


async def main_async():
    """Main asynchronous function for the application logic."""
    logger.info("Starting IronFlock Publisher application...")

    if not DEVICE_KEY:
        logger.error(
            "DEVICE_KEY is not set. It is normally injected by the IronFlock "
            "platform; for a local run, export DEVICE_KEY before starting. Exiting."
        )
        sys.exit(1)

    await register_device()

    global main_asyncio_loop
    main_asyncio_loop = asyncio.get_running_loop()

    # MQTT Client Setup
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect  # Assign disconnect handler

    # If authentication is needed for Mosquitto
    # MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
    # MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
    # if MQTT_USERNAME and MQTT_PASSWORD:
    #     client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    #     logger.info("MQTT authentication enabled.")

    # Retry the initial connection with backoff instead of exiting: the broker
    # may not be ready yet when this container starts. Once connected, paho's
    # loop_start() handles automatic reconnection.
    backoff = 1
    max_backoff = 30
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            break
        except (ConnectionRefusedError, OSError) as e:
            logger.warning(
                f"MQTT broker not reachable at {MQTT_BROKER}:{MQTT_PORT} ({e}); "
                f"retrying in {backoff}s."
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

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
        await asyncio.sleep(3600)  # Sleep for a long time, or indefinitely


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
        logger.error(
            f"An unexpected error occurred during IronFlock execution: {e}",
            exc_info=True,
        )
        sys.exit(1)

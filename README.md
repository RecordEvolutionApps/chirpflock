# ChirpFlock App

**Description:**

ChirpFlock is based on the [ChirpStack](https://www.chirpstack.io/) open source project and provides a complete, open-source LoRaWAN Network Server solution. It simplifies the deployment and management of LoRaWAN networks, bringing powerful connectivity to your IoT projects. ChirpFlock adds IronFlock integration to ChirpStack: secured remote access to the ChirpStack user interface, fleet-wide parametrisation, and automatic data collection for immediate dashboarding in IronFlock.

![ChirpStack Logo and LoRaWAN Devices](https://www.chirpstack.io/img/chirpstack.png)

**Key Features:**

* **LoRaWAN Network Server:** Fully compliant with the LoRaWAN specification.
* **Device Management:** Register, configure, and manage your LoRaWAN end-devices.
* **Web-Based Interface:** User-friendly web interface for network management and monitoring.
* **IronFlock data collection:** Uplinks are automatically forwarded into your fleet's private TimescaleDB for dashboarding.
* **Open Source & Scalable:** Built on open-source principles; handles deployments from small to large.

## Architecture

ChirpFlock is a Docker Compose bundle. The services (see `docker-compose.yml`):

| Service | Purpose | Base image |
| --- | --- | --- |
| `chirpstack` | LoRaWAN Network Server + Web UI + REST/gRPC API | `chirpstack/chirpstack:4.18.0` |
| `chirpstack-gateway-bridge` | Semtech UDP packet-forwarder bridge | `chirpstack/chirpstack-gateway-bridge:4.0.11` |
| `chirpstack-gateway-bridge-basicstation` | BasicStation (CUPS / LNS) bridge | `chirpstack/chirpstack-gateway-bridge:4.0.11` |
| `mosquitto` | MQTT broker (internal bus between ChirpStack and the bridges) | `eclipse-mosquitto:2.0.21` |
| `postgres` | ChirpStack database (TimescaleDB extensions) | `postgres:14-alpine` |
| `redis` | ChirpStack cache / device session store | `redis:7-alpine` |
| `ironflock_publisher` | Subscribes to ChirpStack uplinks over MQTT and publishes them to the IronFlock fleet DB over WAMP | `python:3.12-slim` |

**Data flow:** Gateway → gateway bridge → `mosquitto` → `chirpstack` (decodes, persists) → publishes the uplink event to MQTT → `ironflock_publisher` transforms it and calls `publish_to_table("sensordata", …)` against the IronFlock WAMP cluster. On startup the publisher also registers the device's remote-access URL into the `devices` table. The table schemas are defined in `.ironflock/data-template.yml`.

### Ports

| Port | Service | Exposed remotely? |
| --- | --- | --- |
| 47836 (http) | ChirpStack Web UI + REST + gRPC | yes (main / quick-access) |
| 1700 (udp) | Gateway Base Station — Semtech UDP | yes |
| 47830 (http) | Gateway Base Station — CUPS / LNS | yes |
| 1883 (tcp) | MQTT broker | **no** — internal only (anonymous access; not published) |

Remote access is declared in `.ironflock/port-template.yml` and is enabled per-device by an administrator on the IronFlock platform.

## Configuration

User-facing settings are declared in `.ironflock/env-template.yml`:

* **`APPLICATION_ID`** — ID of a ChirpStack Application (created in the UI under a tenant). Only uplinks from this application are collected into IronFlock. Leave empty to collect from all applications.

The IronFlock platform also injects system variables automatically — notably **`DEVICE_KEY`**, used by the publisher to build the device's remote-access URL. You do not configure these.

### Default credentials

* **ChirpStack admin:** `admin` / `admin` — change the password in the ChirpStack web UI after first login.
* **PostgreSQL** and the **ChirpStack API/JWT secret** are not committed. Postgres credentials default to `chirpstack/chirpstack/chirpstack` and can be overridden with the `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` environment variables. The API secret and the gateway CA are generated once per deployment by `configuration/chirpstack/entrypoint.sh` and persisted in the `chirpstackcerts` volume.

## Getting Started

1. **Installation:** Install the ChirpFlock app from the IronFlock App Store onto a device in your fleet.
2. **Remote access:** Enable remote access to port 47836 for the device, then open the app to reach the ChirpStack UI.
3. **Configuration:** Log in to ChirpStack (`admin` / `admin`), create a tenant, an application, and a device profile, and register your end-devices.
4. **Data collection:** Set `APPLICATION_ID` in the app settings to the application you want collected into IronFlock.
5. **Dashboard:** View incoming data in IronFlock.

### Local development

```bash
# DEVICE_KEY is normally injected by the IronFlock platform; set a placeholder
# to run the publisher locally (it will start but won't reach the real WAMP realm).
export DEVICE_KEY=local-dev

docker compose build
docker compose up
```

ChirpStack will be available at http://localhost:47836. The MQTT broker is not published to the host by default (see `docker-compose.yml`).

To import the legacy LoRaWAN device repository into the database:

```bash
make import-lorawan-devices
```

## Requirements

* **Host:** A device managed by IronFlock with Docker support (the standard IronFlock runtime).
* **Architecture:** linux/amd64 or linux/arm64 (the upstream ChirpStack images publish both).
* **Network:** LoRaWAN gateways must be able to reach the device on UDP 1700 (Semtech) and/or 47830 (BasicStation), typically via IronFlock remote access.

## Support and Resources

* **ChirpStack Official Website:** [https://www.chirpstack.io/](https://www.chirpstack.io/)
* **ChirpStack Community Forum:** [https://forum.chirpstack.io/](https://forum.chirpstack.io/)
* **Documentation:** [https://www.chirpstack.io/docs/](https://www.chirpstack.io/docs/)

## License

ChirpStack is released under the MIT License (see `LICENSE`). This app provides a convenient way to deploy and manage ChirpStack on IronFlock. Refer to the official ChirpStack documentation for advanced configuration.

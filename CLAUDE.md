# CLAUDE.md

Guidance for working in this repo. For the user-facing overview, see `README.md`.

## What this is

ChirpFlock is **not a typical app** — it's a Docker Compose bundle that wraps
upstream [ChirpStack](https://www.chirpstack.io/) (LoRaWAN Network Server) and
adds an IronFlock integration. There is no root build system / package.json. The
only first-party application code is one small Python service; everything else is
configuration around stock images.

## Where things live

| Path | What it is | Edit freely? |
| --- | --- | --- |
| `ironflock_publish/ironflock_publisher.py` | The only real app code: MQTT→WAMP bridge that forwards ChirpStack uplinks to the IronFlock fleet DB | yes |
| `configuration/chirpstack/chirpstack.toml` | Main ChirpStack config | yes, carefully |
| `configuration/chirpstack/entrypoint.sh` | Generates per-deployment secret + gateway CA at container start, drops privileges | yes, carefully |
| `configuration/chirpstack/region_*.toml` | Stock ChirpStack regional band configs (~40 files) | only if you must; don't hand-edit en masse |
| `configuration/chirpstack-gateway-bridge/*` | Stock gateway-bridge config | rarely |
| `configuration/mosquitto/`, `configuration/postgresql/` | Broker + DB image config | rarely |
| `.ironflock/*.yml` | IronFlock platform templates (see below) | yes |
| `docker-compose.yml` | Service wiring, healthchecks, volumes | yes |

### `.ironflock/` platform templates
- `env-template.yml` — the settings **form** shown to users; each top-level key becomes an env var injected into the containers.
- `data-template.yml` — defines the cloud **TimescaleDB tables** (`sensordata`, `devices`) the app writes to.
- `port-template.yml` — declares which ports may be exposed via IronFlock remote access.
- `board-template.yml` — the default IronFlock dashboard.

## Commands

```bash
docker compose build                      # build all images (CI runs this)
export DEVICE_KEY=local-dev               # publisher needs this locally (see below)
docker compose up                         # run the full stack; UI at http://localhost:47836
docker compose config -q                  # validate compose file
uvx ruff check ironflock_publish          # lint the publisher (CI runs this)
python -m py_compile ironflock_publish/ironflock_publisher.py
make import-lorawan-devices               # import the legacy LoRaWAN device repo into the DB
```

CI (`.github/workflows/ci.yml`) runs ruff + py_compile + `compose config` + `compose build`.

## How it runs (deployment model)

On the IronFlock platform, env-template fields **and system variables are injected
into the containers at runtime** — `docker-compose.yml` does not wire them (only
defaults). Consequences:
- **`DEVICE_KEY`** is a platform-injected system var (used to build the device's
  remote-access URL). It is *not* in `env-template.yml`. Locally you must
  `export DEVICE_KEY=...` or the publisher exits with a clear error.
- **`APPLICATION_ID`** is the one user-facing setting (filters which ChirpStack
  application's uplinks are collected; empty = all).

## Data flow (mosquitto is required for data collection)

```
device → gateway → gateway-bridge → mosquitto → chirpstack  (decodes, persists to Postgres)
                                                    │ chirpstack MQTT integration republishes uplink
                                                    ▼
                         mosquitto → ironflock_publisher → WAMP → IronFlock fleet DB
```

`ironflock_publisher` subscribes to `application/+/device/+/event/up` on the
broker — it is the broker's most important consumer and the **only** source of
IronFlock data. All services reach the broker internally as `mosquitto:1883`; it
is intentionally not published to the host or exposed remotely (anonymous access).

## Gotchas / invariants (don't regress these)

- **Never hardcode or commit secrets.** The ChirpStack JWT `secret` and the
  gateway CA are generated once per deployment by `entrypoint.sh` into the
  `chirpstackcerts` volume. `chirpstack.toml` uses `secret="$API_SECRET"`.
  Changing the secret invalidates all existing login/API tokens.
- **ChirpStack does env-var substitution inside `.toml`** — that's why `$VAR`
  works in `chirpstack.toml` (e.g. `$API_SECRET`, `$POSTGRESQL_USER`,
  `$MQTT_BROKER_HOST`). Pass new config via env + `$VAR` rather than hardcoding.
- **Postgres credentials** come from `POSTGRES_USER/PASSWORD/DB` (default
  `chirpstack`) and must stay in sync between the `postgres` and `chirpstack`
  services in `docker-compose.yml`.
- **`transform_payload()` keys must match `data-template.yml`.** Each key in the
  dict the publisher sends maps to a `path: args[0].<key>` column in the
  `sensordata` table. Add/rename a field → change both, or it silently drops.
- **The chirpstack Dockerfile copies only `chirpstack.toml region_*.toml`** into
  `/etc/chirpstack/` (so build files don't leak in). Do **not** add a
  `.dockerignore` that excludes `entrypoint.sh` — a `.dockerignore` entry can't
  be `COPY`ed, which breaks `COPY entrypoint.sh /entrypoint.sh`.
- **The entrypoint drops to `65534:65533`** (nobody:nogroup) via `su-exec` after
  provisioning. `openssl` and `su-exec` are added in the Dockerfile (not in the
  base image).
- **Pin base image versions** (already done); keep them pinned.

## Verifying a change

For anything touching the chirpstack image, entrypoint, or compose wiring, run
the stack and check it actually comes up:

```bash
export DEVICE_KEY=local-dev
docker compose up -d chirpstack            # brings up postgres/redis/mosquitto (healthchecked) too
docker compose ps                          # all should reach healthy
docker compose logs chirpstack | grep '\[entrypoint\]'   # confirm secret/CA provisioning + privilege drop
docker compose down -v
```

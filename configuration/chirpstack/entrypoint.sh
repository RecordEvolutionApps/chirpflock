#!/bin/sh
# ChirpStack container entrypoint.
#
# Runs as root only long enough to provision per-deployment secrets into the
# persistent `certs` volume, then drops privileges to the unprivileged user
# (65534 / nobody) to run ChirpStack itself.
#
# What is provisioned here (and why it is NOT baked into the image / committed):
#   * Gateway CA key + cert  -> used by ChirpStack to sign BasicStation client
#                               certificates. Must be stable per deployment and
#                               secret; baking it into the image would leak the
#                               private key in an image layer.
#   * API/JWT secret         -> signs login and API tokens. Must be stable per
#                               deployment (changing it logs everyone out) and
#                               unique (a committed shared secret lets anyone
#                               forge admin tokens for every install).
set -e

CERT_DIR=/etc/chirpstack/certs
CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"
SECRET_FILE="$CERT_DIR/api_secret"
# Matches the base image's default user (nobody:nogroup = 65534:65533).
RUN_UID=65534
RUN_GID=65533

mkdir -p "$CERT_DIR"

# --- Gateway CA certificate ---------------------------------------------------
if [ ! -f "$CA_KEY" ] || [ ! -f "$CA_CERT" ]; then
  echo "[entrypoint] Generating gateway CA certificate..."
  openssl genrsa -out "$CA_KEY" 4096
  openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 1825 -out "$CA_CERT" \
    -subj "/C=DE/ST=Hessen/L=Frankfurt/O=IronFlock/CN=IronFlock CA"
else
  echo "[entrypoint] Using existing gateway CA certificate."
fi

# --- API / JWT secret ---------------------------------------------------------
# Precedence: an externally injected API_SECRET wins (lets the platform manage
# it); otherwise reuse the persisted one; otherwise generate a fresh one.
if [ -n "$API_SECRET" ]; then
  echo "[entrypoint] Using API_SECRET from environment."
  printf '%s' "$API_SECRET" > "$SECRET_FILE"
elif [ ! -f "$SECRET_FILE" ]; then
  echo "[entrypoint] Generating API secret..."
  openssl rand -base64 32 > "$SECRET_FILE"
else
  echo "[entrypoint] Using existing API secret."
fi
API_SECRET="$(cat "$SECRET_FILE")"
export API_SECRET

# --- Permissions --------------------------------------------------------------
chmod 600 "$CA_KEY" "$SECRET_FILE"
chmod 644 "$CA_CERT"
chown -R "$RUN_UID:$RUN_GID" "$CERT_DIR"

echo "[entrypoint] Starting ChirpStack as ${RUN_UID}:${RUN_GID}..."
exec su-exec "$RUN_UID:$RUN_GID" chirpstack "$@"

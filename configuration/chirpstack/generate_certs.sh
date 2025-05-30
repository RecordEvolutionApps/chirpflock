#!/bin/sh

CERT_DIR=/etc/chirpstack/certs
CA_KEY=$CERT_DIR/ca.key
CA_CERT=$CERT_DIR/ca.crt

mkdir -p "$CERT_DIR"

# Generate CA cert if not present
if [ ! -f "$CA_KEY" ] || [ ! -f "$CA_CERT" ]; then
  echo "[INFO] Generating CA certificate..."
  openssl genrsa -out "$CA_KEY" 4096
  openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 1825 -out "$CA_CERT" \
    -subj "/C=DE/ST=Hessen/L=Frankfurt/O=IronFlock/CN=IronFlock CA"
else
  echo "[INFO] Using existing CA certificate."
fi

chown chirpstack:chirpstack /etc/chirpstack/certs/ca.key
chown chirpstack:chirpstack /etc/chirpstack/certs/ca.crt
chmod 600 /etc/chirpstack/certs/ca.key
chmod 644 /etc/chirpstack/certs/ca.crt
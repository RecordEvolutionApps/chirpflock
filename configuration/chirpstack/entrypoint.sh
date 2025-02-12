#! /bin/bash

git clone https://github.com/brocaar/lorawan-devices /tmp/lorawan-devices
chirpstack -c /etc/chirpstack import-legacy-lorawan-devices-repository -d /tmp/lorawan-devices

exec /usr/bin/chirpstack -c /etc/chirpstack
FROM chirpstack/chirpstack:4.18.0

USER root
# openssl: generate the gateway CA + API secret at runtime (see entrypoint.sh).
# su-exec: drop back to the unprivileged user after provisioning.
RUN apk add --no-cache openssl su-exec

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Config only (chirpstack.toml + region_*.toml) — copied explicitly so build
# files (Dockerfile, entrypoint.sh) don't leak into the config dir. Secrets are
# NOT baked in; they are generated at container start into the `certs` volume.
COPY chirpstack.toml region_*.toml /etc/chirpstack/

ENTRYPOINT ["/entrypoint.sh"]

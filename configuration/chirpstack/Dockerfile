FROM chirpstack/chirpstack:4

COPY . /etc/chirpstack/

USER root

RUN apk add --no-cache git && \
    git clone https://github.com/brocaar/lorawan-devices /tmp/lorawan-devices

USER 65534

# ENTRYPOINT [ "/entrypoint.sh" ]


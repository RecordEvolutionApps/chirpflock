FROM chirpstack/chirpstack:4.18.0

USER root
RUN apk update && apk add openssl

COPY generate_certs.sh /generate_certs.sh

RUN /generate_certs.sh

USER 65534

COPY . /etc/chirpstack/

# ENTRYPOINT [ "/entrypoint.sh" ]


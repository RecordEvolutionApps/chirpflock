FROM chirpstack/chirpstack:4.12.1

COPY . /etc/chirpstack/

COPY generate_certs.sh /generate_certs.sh

USER root
RUN apk update && apk add openssl

RUN /generate_certs.sh

USER 65534

# ENTRYPOINT [ "/entrypoint.sh" ]


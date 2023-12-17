############################
# Docker build environment #
############################

FROM golang:alpine AS build

WORKDIR /build

COPY src .

RUN go get -d -v && \
    go build -o bonjourmadame-api-server

############################
# Docker final environment #
############################

#FROM scratch
FROM golang:alpine

LABEL name="BonjourMadame API Server" \
      website="https://bonjourmadame.xorhak.fr" \
      repository="https://github.com/djerfy/bonjourmadame-api-server" \
      maintainer="Djerfy <djerfy@gmail.com>" \
      contributor="Azrod <contact@mickael-stanislas.com>"

WORKDIR /app

ENV VERSION="2.0.0"
ENV GIN_MODE="release"

COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /build/bonjourmadame-api-server ./bonjourmadame-api-server
COPY --from=build /build/static ./static
COPY --from=build /build/templates ./templates

CMD ["/app/bonjourmadame-api-server"]

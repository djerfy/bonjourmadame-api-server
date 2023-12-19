############################
# Docker build environment #
############################

FROM golang:alpine AS build

WORKDIR /build

COPY . .

RUN go mod tidy && \
    go build -o bonjourmadame-api-server

############################
# Docker final environment #
############################

FROM scratch

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
COPY --from=build /build/resources/static ./static
COPY --from=build /build/resources/templates ./templates

CMD ["/app/bonjourmadame-api-server"]

############################
# Docker build environment #
############################

FROM python:3.11-slim AS build

WORKDIR /usr/app

ENV PATH="/usr/app/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential gcc && \
    python -m venv /usr/app/venv

COPY requirements.txt .

RUN pip install -r requirements.txt

############################
# Docker final environment #
############################

FROM python:3.11-slim

LABEL name="BonjourMadame API Server" \
      website="https://bonjourmadame.xorhak.fr" \
      repository="https://github.com/djerfy/bonjourmadame-api-server" \
      maintainer="Djerfy <djerfy@gmail.com>" \
      contributor="Azrod <contact@mickael-stanislas.com>"

WORKDIR /usr/app

ENV VERSION="1.9.20"
ENV FLASK_APP="bm-api-server.py"
ENV FLASK_DEBUG="False"
ENV PYTHONUNBUFFERED="True"
ENV PATH="/usr/app/venv/bin:$PATH"

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python && \
    apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/{apt,dpkg,cache,log} && \
    mkdir -p /usr/app && \
    chown python:python /usr/app

COPY --chown=python:python --from=build /usr/app/venv ./venv
COPY --chown=python:python ./src/ .

USER 999

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "bm-api-server:app", "--capture-output", "--log-level", "info", "--timeout", "900"]

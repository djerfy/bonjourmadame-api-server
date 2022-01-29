FROM python:3.10-slim as build
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    build-essential gcc 

WORKDIR /usr/app
RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM python:3.10-slim@sha256:2bac43769ace90ebd3ad83e5392295e25dfc58e58543d3ab326c3330b505283d

LABEL name="BonjourMadame API Server" \
    maintainer="Djerfy <djerfy@gmail.com>"

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python

RUN mkdir /usr/app && chown python:python /usr/app
WORKDIR /usr/app

COPY --chown=python:python --from=build /usr/app/venv ./venv
COPY --chown=python:python ./src/ .

ENV VERSION=1.9.7
ENV FLASK_APP=bm-api-server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=TRUE

USER 999

ENV PATH="/usr/app/venv/bin:$PATH"
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "bm-api-server:app","--capture-output", "--log-level", "debug" ]
# CMD [ "/bin/bash" ]
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f https://localhost:5000/health

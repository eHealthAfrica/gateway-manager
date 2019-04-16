FROM python:3.7-slim-stretch

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc && \
    pip install -q --upgrade pip && \
    pip install -q python-keycloak pyjwt

WORKDIR /code
COPY . /code

ENTRYPOINT ["/code/entrypoint.sh"]

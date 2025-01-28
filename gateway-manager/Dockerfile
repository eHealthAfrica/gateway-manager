FROM python:3.8-slim-buster

LABEL description="GWM > Kong+Keycloak installation tool" \
      name="gateway-manager" \
      author="eHealth Africa"

ENTRYPOINT ["/code/entrypoint.sh"]
WORKDIR /code

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc git curl
#    curl -L https://cnfl.io/ccloud-cli | sh -s -- -b /usr/local/bin

COPY ./conf/pip /code/conf/pip

RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

COPY . /code

ARG VERSION
ARG REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $REVISION > /var/tmp/REVISION

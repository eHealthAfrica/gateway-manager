FROM python:3.8-slim-buster

WORKDIR /code

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc git curl

RUN curl -L https://cnfl.io/ccloud-cli | sh -s -- -b /usr/local/bin

COPY ./conf/pip /code/conf/pip

RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

COPY . /code

ARG VERSION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

ENTRYPOINT ["/code/entrypoint.sh"]

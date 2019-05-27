FROM python:3.7-slim-stretch

WORKDIR /code

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc

COPY . /code

RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt


ENTRYPOINT ["/code/entrypoint.sh"]

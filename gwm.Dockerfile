################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./gateway-manager/conf/docker/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


################################################################################
## using node image to build react app
################################################################################

FROM node:lts-slim AS app_node

## copy application version and git revision
COPY --from=app_resource /tmp/resources/. /var/tmp/

WORKDIR /node

COPY ./gateway-manager/home/app /node
RUN npm install -q && npm run build


################################################################################
## using python image to build app
###############################################################################

FROM python:3.8-slim-buster

LABEL description="GWM > Kong+Keycloak installation tool" \
      name="gateway-manager" \
      author="eHealth Africa"

WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

COPY ./gateway-manager /code
RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc git curl && \
    curl -L https://cnfl.io/ccloud-cli | sh -s -- -b /usr/local/bin && \
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt && \
    mkdir -p /var/tmp && \
    rm -Rf /code/home/app/build/

## copy react app
COPY --from=app_node /node/build/. /code/build/

## copy application version and git revision
COPY --from=app_resource /tmp/resources/. /var/tmp/

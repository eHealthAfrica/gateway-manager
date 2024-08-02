################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./gateway-manager/conf/docker/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


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
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt && \
    mkdir -p /var/tmp

## copy application version and git revision
COPY --from=app_resource /tmp/resources/. /var/tmp/

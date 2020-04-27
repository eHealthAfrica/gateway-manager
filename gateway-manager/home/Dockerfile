FROM node:lts-slim

ARG VERSION=0.0.0
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION

WORKDIR /code/app/

COPY ./app /code/app
RUN npm install -q -g npm && npm install -q
ENV PATH /code/app/node_modules/.bin:$PATH

COPY ./conf /code/conf

ENTRYPOINT ["/code/conf/entrypoint.sh"]

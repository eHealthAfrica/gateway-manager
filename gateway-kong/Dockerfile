FROM kong:latest

# Kong install dir
ENV KONG_OIDC_HOME /usr/local/share/lua/5.1/kong/plugins/kong-oidc-auth
ENV KONG_OIDC_REPO https://github.com/eHealthAfrica/kong-oidc-auth.git

# Install OIDC plugin
RUN apk -U add --no-cache --virtual .build-deps git unzip gcc libc-dev openssl-dev && \
    git clone $KONG_OIDC_REPO $KONG_OIDC_HOME && \
    cd $KONG_OIDC_HOME && \
    luarocks make *.rockspec && \
    apk del .build-deps

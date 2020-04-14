ARG VERSION=latest
FROM kong:$VERSION

# Kong install dir
ENV KONG_OIDC_HOME /usr/local/share/lua/5.1/kong/plugins/kong-oidc-auth
ENV KONG_OIDC_REPO https://github.com/eHealthAfrica/kong-oidc-auth.git

# In version 2.0 the active user is kong
# we need to switch back to root to install the plugin
USER root

# Install OIDC plugin
RUN apk -U add --no-cache --virtual .build-deps git unzip gcc libc-dev openssl-dev && \
    git clone $KONG_OIDC_REPO $KONG_OIDC_HOME && \
    cd $KONG_OIDC_HOME && \
    luarocks make *.rockspec && \
    apk del .build-deps

# Patch nginx kong template file
ENV TEMPLATES_DIR="/usr/local/share/lua/5.1/kong/templates"
COPY ./nginx_templates/ $TEMPLATES_DIR/

RUN cp $TEMPLATES_DIR/nginx_kong.lua $TEMPLATES_DIR/nginx_kong.lua.original && \
    sed -i \
    "/Kong.rewrite\(\)/r $TEMPLATES_DIR/nginx_kong.lua.patch" \
    $TEMPLATES_DIR/nginx_kong.lua

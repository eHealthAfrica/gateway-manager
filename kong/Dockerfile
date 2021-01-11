ARG VERSION=latest
FROM kong:$VERSION

# In version 2.0 the active user is kong
# we need to switch back to root to install the plugin
USER root

# Install custom OIDC plugin
ENV KONG_OIDC_HOME /usr/local/share/lua/5.1/kong/plugins/kong-oidc-auth
COPY ./kong-oidc-auth $KONG_OIDC_HOME/

RUN apk -U add --no-cache --virtual .build-deps unzip gcc libc-dev openssl-dev && \
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

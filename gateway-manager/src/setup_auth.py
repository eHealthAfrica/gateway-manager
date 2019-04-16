#!/usr/bin/env python

# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from helpers import request
from settings import HOST, KONG_URL, KEYCLOAK_INTERNAL, MINIO_INTERNAL


def register_app(name, url):
    # Register Client with Kong
    # Single API Service
    data = {
        'name': name,
        'url': url,
    }
    client_info = request(method='post', url=f'{KONG_URL}/services/', data=data)
    client_id = client_info['id']

    # ADD CORS Plugin to Kong for whole domain CORS
    PLUGIN_URL = f'{KONG_URL}/services/{name}/plugins'
    data_cors = {
        'name': 'cors',
        'config.credentials': 'true',
        'config.exposed_headers': 'Authorization',
        'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
        'config.max_age': 3600,
        'config.methods': ['HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        'config.origins': f'{HOST}/*',
    }
    request(method='post', url=PLUGIN_URL, data=data_cors)

    # Routes
    # Add a route which we will NOT protect
    ROUTE_URL = f'{KONG_URL}/services/{name}/routes'
    data_route = {
        'paths' : [f'/{name}'],
        'strip_path': 'false',
        'preserve_host': 'false',  # This is keycloak specific.
    }
    request(method='post', url=ROUTE_URL, data=data_route)

    return client_id


if __name__ == '__main__':
    # add keycloak and minio
    services = [
        ('keycloak', KEYCLOAK_INTERNAL),
        ('minio', MINIO_INTERNAL),
    ]

    for name, url in services:
        print(f'Exposing service "{name}" @ {url}')
        register_app(name, url)
        print(f'Service "{name}" @ {url} now being served by kong @ {HOST}/{name}')

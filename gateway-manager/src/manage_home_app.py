#!/usr/bin/env python

# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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

import sys

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
)

from decode_token import get_userinfo
from helpers import get_logger, load_json_file
from manage_keycloak import get_realm_display_name
from manage_kong import get_services_by_realm
from settings import (
    BASE_HOST,
    KONG_PUBLIC_REALM,
    KONG_TOKEN_HEADER,
    REVISION,
    SERVICES_DATA_PATH,
    VERSION,
    WEB_SERVER_PORT,
    WEB_SERVICE_NAME,
)

HOST = '0.0.0.0'
LOGGER = get_logger('HOME')
app = None

STATIC_URL = f'/{KONG_PUBLIC_REALM}/{WEB_SERVICE_NAME}/static'
try:
    SERVICES = load_json_file(SERVICES_DATA_PATH, {
        'host': BASE_HOST,
        'public_realm': KONG_PUBLIC_REALM,
    })
except Exception:
    SERVICES = {}


def start_app():
    app = Flask(
        '__main__',
        template_folder='../templates',
        static_folder='../static',
        static_url_path=STATIC_URL,
    )

    @app.route(f'/{KONG_PUBLIC_REALM}/{WEB_SERVICE_NAME}/health', methods=['GET'])
    def _health():
        # health endpoint, returns current commit hash and version
        return jsonify(version=VERSION, revision=REVISION)

    @app.route('/<realm>/', methods=['GET'])
    def _index(realm):
        # landing page
        realm_name = get_realm_display_name(realm)
        available_services = get_services_by_realm(realm)
        services = [
            value
            for key, value in SERVICES.items()
            if key in available_services
        ]

        username = get_userinfo(request.headers.get(KONG_TOKEN_HEADER))
        return render_template(
            'landing-page.html',
            # realm urls
            account_url=f'{BASE_HOST}/auth/realms/{realm}/account',
            base_url=f'{BASE_HOST}/{realm}',
            logout_url=f'{BASE_HOST}/{realm}/{WEB_SERVICE_NAME}/logout',
            static_url=f'{BASE_HOST}{STATIC_URL}',
            # realm & user info
            tenant=realm_name,
            username=username,
            services=services,
        )

    @app.route(f'/<realm>/{WEB_SERVICE_NAME}/', methods=['GET'])
    def _index_2(realm):
        # this is the url used after logout, redirect to /<realm>
        return redirect(f'/{realm}')

    app.run(host=HOST, port=WEB_SERVER_PORT)
    LOGGER.info(f'App started on {HOST}:{WEB_SERVER_PORT}')


if __name__ == '__main__':
    COMMANDS = {
        'START_APP': start_app,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    try:
        fn = COMMANDS[command]
        fn()
    except Exception as e:
        LOGGER.error(str(e))
        sys.exit(1)

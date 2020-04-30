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

import json
import os
import sys

from time import sleep
from flask import Flask, render_template, send_from_directory
from helpers import check_realm, get_logger, request

from settings import CDN_URL, WEB_SERVER_PORT, BASE_HOST, KONG_INTERNAL_URL
from manage_kong import _check_404

LOGGER = get_logger('HOME')
app = None


def start_app():
    cdn = CDN_URL
    if cdn:
        if cdn.endswith('/'):
            cdn = cdn[:-1]
        assets_location = '/code/build/asset-manifest.json'
        with open(assets_location, 'rb') as fp:
            assets = json.load(fp)
        for asset in assets['files']:
            assets['files'][asset] = f'{cdn}{assets["files"][asset]}'

        with open(assets_location, 'w') as fp:
            json.dump(assets, fp)

        index_location = '/code/build/index.html'
        with open(index_location, 'r') as fp:
            index = fp.read()
        new_index = index.replace('/static', f'{cdn}/static') \
            .replace('/aether.ico', f'{cdn}/aether.ico')

        with open(index_location, 'w') as fp:
            fp.write(new_index)

    app = Flask(
        '__main__',
        template_folder='../build',
        static_folder='../build',
        static_url_path='/gateway'
    )

    @app.route('/<realm>/', methods=['GET'])
    def index(realm):
        services = []
        url = f'{KONG_INTERNAL_URL}/services'
        if not _check_404(url):
            res = request(method='get', url=url)
            services = res['data'] if 'data' in res else []
        return render_template('index.html', services=json.dumps(services))

    HOST = '0.0.0.0'
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

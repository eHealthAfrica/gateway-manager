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

from requests.auth import HTTPBasicAuth
import sys

from helpers import (
    do_nothing,
    get_logger,
    load_json_file,
    request,
)
from settings import (
    ES_HOST,
    ES_USER,
    ES_PW,
    TEMPLATES,
)

API = f'{ES_HOST}/_opendistro/_security/api/'
LOGGER = get_logger('ElasticSearch')


def create_tenant(tenant, version=6):
    ROLES_URL = f'{API}roles/{tenant}'
    if version < 7:
        role = load_json_file(TEMPLATES['es']['role'], {'tenant': tenant})
    else:
        role = load_json_file(TEMPLATES['es7']['role'], {'tenant': tenant})
    ok = request(method='put', url=ROLES_URL, auth=AUTH, json=role)
    LOGGER.info(f'tenant role: {ok}')

    ROLES_MAPPING_URL = f'{API}rolesmapping/{tenant}'
    if version < 7:
        mapping = {'backendroles': [tenant]}
    else:
        mapping = {'backend_roles': [tenant]}
    ok = request(method='put', url=ROLES_MAPPING_URL, auth=AUTH, json=mapping)
    LOGGER.info(f'rolesmapping: {ok}')


def setup_es():
    OWN_INDEX_URL = f'{API}rolesmapping/own_index'
    ok = request(method='delete', url=OWN_INDEX_URL, auth=AUTH)
    LOGGER.info(f'remove user indexes: {ok}')


def is_es_ready():
    try:
        request(method='get', url=ES_HOST, auth=AUTH)
        LOGGER.success('ElasticSearch is ready!')
    except Exception as e:
        LOGGER.critical('ElasticSearch is NOT ready!')
        raise e


if __name__ == "__main__":
    COMMANDS = {
        'READY': do_nothing,
        'ADD_TENANT': create_tenant,
        'SETUP': setup_es,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    try:
        AUTH = HTTPBasicAuth(ES_USER, ES_PW)
        is_es_ready()

        fn = COMMANDS[command]
        args = sys.argv[2:]
        fn(*args)
    except Exception as e:
        LOGGER.error(str(e))
        sys.exit(1)

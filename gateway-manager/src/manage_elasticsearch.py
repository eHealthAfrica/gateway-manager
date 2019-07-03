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

from helpers import get_logger, request
from settings import (
    ES_HOST,
    ES_USER,
    ES_PW
)

AUTH = HTTPBasicAuth(ES_USER, ES_PW)
API = f'{ES_HOST}/_opendistro/_security/api/'


def create_tenant(tenant):

    role = {
        'cluster': [
            'INDICES_MONITOR',
            'CLUSTER_COMPOSITE_OPS'
        ],
        'indices': {
            '*': {
                '*': [
                    'indices:data/read/field_caps*',
                    'indices:data/read/xpack/rollup*',
                    'indices:admin/mappings/get*'
                ]
            },
            f'?kibana*{tenant}': {
                '*': ['MANAGE', 'INDEX', 'READ', 'DELETE']
            },
            '?management-beats': {
                '*': [
                    'INDICES_ALL'
                ]
            },
            '?tasks': {
                '*': [
                    'INDICES_ALL'
                ]
            },
            f'{tenant}*': {
                '*': [
                    'UNLIMITED'
                ]
            }
        },
        'tenants': {
            tenant: 'RW'
        }
    }

    url = f'{API}roles/{tenant}'
    ok = request(method='put', url=url, auth=AUTH, json=role)
    logger.info(f'tenant role: {ok}')

    mapping = {
        'backendroles': [
            tenant
        ]
    }
    url = f'{API}rolesmapping/{tenant}'
    ok = request(method='put', url=url, auth=AUTH, json=mapping)
    logger.info(f'rolesmapping: {ok}')


def setup_es():
    __remove_own_index()


def __remove_own_index():
    url = f'{API}rolesmapping/own_index'
    ok = request(method='delete', url=url, auth=AUTH)
    logger.info(f'remove user indexes: {ok}')


if __name__ == "__main__":
    logger = get_logger('ElasticSearch')

    COMMANDS = {
        'ADD_TENANT': create_tenant,
        'SETUP': setup_es
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        logger.critical(f'No command: {command}')
        sys.exit(1)

    fn = COMMANDS[command]
    args = sys.argv[2:]
    fn(*args)

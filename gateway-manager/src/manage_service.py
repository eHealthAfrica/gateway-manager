#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

import fnmatch
import json
import os
import sys

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
from requests.exceptions import HTTPError

from helpers import request
from settings import (
    HOST,
    DOMAIN,

    KONG_URL,
    KONG_OIDC_PLUGIN,

    KC_URL,
    KC_ADMIN_USER,
    KC_ADMIN_PASSWORD,
    KC_MASTER_REALM,
    KEYCLOAK_KONG_CLIENT,

    SERVICES_PATH,
    SOLUTIONS_PATH,
)

# endpoint types
EPT_OIDC = 'oidc'
EPT_PUBLIC = 'public'


def _get_service_oidc_payload(service_name, realm):
    client_id = KEYCLOAK_KONG_CLIENT
    client_secret = None

    # must be the public url
    KEYCLOAK_URL = f'{HOST}/keycloak/auth/realms'
    OPENID_PATH = 'protocol/openid-connect'

    try:
        # https://bitbucket.org/agriness/python-keycloak

        # find out client secret
        # 1. connect to master realm
        keycloak_admin = KeycloakAdmin(server_url=KC_URL,
                                       username=KC_ADMIN_USER,
                                       password=KC_ADMIN_PASSWORD,
                                       realm_name=KC_MASTER_REALM,
                                       )
        # 2. change to given realm
        keycloak_admin.realm_name = realm
        # 3. get kong client internal id
        client_pk = keycloak_admin.get_client_id(client_id)
        # 4. get its secrets
        secret = keycloak_admin.get_client_secrets(client_pk)
        client_secret = secret.get('value')

    except KeycloakError as ke:
        raise RuntimeError(f'Could not get info from keycloak  {str(ke)}')
    except Exception as e:
        raise RuntimeError(f'Unexpected error, do the realm and the client exist?  {str(e)}')

    # OIDC plugin settings (same for all endpoints)
    return {
        'name': KONG_OIDC_PLUGIN,

        'config.client_id': client_id,
        'config.client_secret': client_secret,
        'config.cookie_domain': DOMAIN,
        'config.email_key': 'email',
        'config.scope': 'openid+profile+email+iss',
        'config.user_info_cache_enabled': 'true',

        'config.app_login_redirect_url': f'{HOST}/{realm}/{service_name}/',
        'config.authorize_url': f'{KEYCLOAK_URL}/{realm}/{OPENID_PATH}/auth',
        'config.service_logout_url': f'{KEYCLOAK_URL}/{realm}/{OPENID_PATH}/logout',
        'config.token_url': f'{KEYCLOAK_URL}/{realm}/{OPENID_PATH}/token',
        'config.user_url': f'{KEYCLOAK_URL}/{realm}/{OPENID_PATH}/userinfo',
    }


def add_service(config, realm):
    name = config['name']  # service name
    host = config['host']  # service host

    print(f'\nAdding realm "{realm}" to service "{name}"')

    # OIDC plugin settings (same for all OIDC endpoints)
    oidc_data = _get_service_oidc_payload(name, realm)

    ep_types = [EPT_PUBLIC, EPT_OIDC]
    for ep_type in ep_types:
        print(f'  Adding "{ep_type}" endpoints')

        endpoints = config.get(f'{ep_type}_endpoints', [])
        for ep in endpoints:
            ep_name = ep['name']
            ep_url = ep['url']
            service_name = f'{name}_{ep_type}_{ep_name}'

            data = {
                'name': service_name,
                'url': f'{host}{ep_url}',
            }
            try:
                request(method='post', url=f'{KONG_URL}/services/', data=data)
                print(f'    + Added service "{ep_name}"')
            except HTTPError:
                print(f'    - Could not add service "{ep_name}"')

            ROUTE_URL = f'{KONG_URL}/services/{service_name}/routes'
            path = ep.get('route_path') or f'/{realm}/{name}{ep_url}'
            route_data = {
                'paths': [path, ],
                'strip_path': ep.get('strip_path', 'false'),
            }
            try:
                route_info = request(method='post', url=ROUTE_URL, data=route_data)

                # OIDC routes are protected using the "kong-oidc-auth" plugin
                if ep_type == EPT_OIDC:
                    protected_route_id = route_info['id']
                    request(
                        method='post',
                        url=f'{KONG_URL}/routes/{protected_route_id}/plugins',
                        data=oidc_data,
                    )

                print(f'    + Added route {ep_url} >> {path}')
            except HTTPError:
                print(f'    - Could not add route {ep_url} >> {path}')

    print(f'Service "{name}" now being served by kong for realm "{realm}"\n')


def remove_service(config, realm):

    def _realm_in_service(realm, service):
        return any([path.strip('/').startswith(realm) for path in service['paths']])

    name = config['name']   # service name
    purge = realm == '*'    # remove service in ALL realms

    if purge:
        print(f'Removing service "{name}" from ALL realms')
    else:
        print(f'Removing service "{name}" from realm {realm}')

    ep_types = [EPT_OIDC, EPT_PUBLIC]
    for ep_type in ep_types:
        print(f'  Removing "{ep_type}" endpoints')

        endpoints = config.get(f'{ep_type}_endpoints', [])
        for ep in endpoints:
            ep_name = ep['name']
            service_name = f'{name}_{ep_type}_{ep_name}'

            routes_url = f'{KONG_URL}/services/{service_name}/routes'
            try:
                res = request(method='get', url=routes_url)
                for service in res['data']:
                    if purge or _realm_in_service(realm, service):
                        ep_des = f'"{ep_name}"  >>  {service["paths"]}'
                        try:
                            request(method='delete', url=f'{KONG_URL}/routes/{service["id"]}')
                            print(f'    + Removed endpoint {ep_des}')
                        except HTTPError:
                            print(f'    - Could not remove endpoint {ep_des}')
            except HTTPError:
                print(f'    - Route not found "{ep_name}"" at {routes_url}')


def load_definitions(def_path):
    definitions = {}
    _files = [f for f in os.listdir(def_path) if fnmatch.fnmatch(f, '*.json')]

    for f in _files:
        with open(f'{def_path}/{f}') as _f:
            config = json.load(_f)
            name = config['name']
            definitions[name] = config
    return definitions


def handle_service(command, name, realm):
    if name not in SERVICE_DEFINITIONS:
        raise KeyError(f'No service definition for name: "{name}"')

    service_config = SERVICE_DEFINITIONS[name]
    if command == 'ADD':
        add_service(service_config, realm)
    elif command == 'REMOVE':
        remove_service(service_config, realm)


def handle_solution(command, name, realm):
    if name not in SOLUTION_DEFINITIONS:
        raise KeyError(f'No solution definition for name: "{name}"')

    services = SOLUTION_DEFINITIONS[name].get('services', [])
    for service in services:
        handle_service(command, service, realm)


if __name__ == '__main__':
    CMDS = ['ADD', 'REMOVE']
    command = sys.argv[1]
    if command not in CMDS:
        raise KeyError(f'No command: {command}')

    TYPES = ['SERVICE', 'SOLUTION']
    service_or_solution = sys.argv[2]
    if service_or_solution not in TYPES:
        raise KeyError(f'No type: {service_or_solution}')

    name = sys.argv[3]
    realm = sys.argv[4]

    SERVICE_DEFINITIONS = load_definitions(SERVICES_PATH)
    if service_or_solution == 'SERVICE':
        handle_service(command, name, realm)

    if service_or_solution == 'SOLUTION':
        SOLUTION_DEFINITIONS = load_definitions(SOLUTIONS_PATH)
        handle_solution(command, name, realm)

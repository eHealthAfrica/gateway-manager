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

import fnmatch
import os
import sys

from typing import Callable, Dict

from requests.exceptions import HTTPError

from manage_keycloak import get_client_secret
from helpers import request, load_json_file, get_logger
from settings import (
    BASE_HOST,
    BASE_DOMAIN,

    KONG_INTERNAL_URL,
    KONG_OIDC_PLUGIN,

    KEYCLOAK_PUBLIC_URL,

    SERVICES_PATH,
    SOLUTIONS_PATH,
    TEMPLATES,
)

# endpoint types
EPT_OIDC = 'oidc'
EPT_PUBLIC = 'public'

ENDPOINT_TYPES = [EPT_PUBLIC, EPT_OIDC]


def _get_service_oidc_payload(service_name, realm, client_id):
    client_secret = get_client_secret(realm, client_id)

    # must be the public url
    _KC_REALMS = f'{KEYCLOAK_PUBLIC_URL}realms'
    _OPENID_PATH = 'protocol/openid-connect'

    # OIDC plugin settings (same for all endpoints)
    return {
        'name': KONG_OIDC_PLUGIN,

        'config.client_id': client_id,
        'config.client_secret': client_secret,
        'config.cookie_domain': BASE_DOMAIN,
        'config.email_key': 'email',
        'config.scope': 'openid+profile+email+iss',
        'config.user_info_cache_enabled': 'true',

        'config.app_login_redirect_url': f'{BASE_HOST}/{realm}/{service_name}/',
        'config.authorize_url': f'{_KC_REALMS}/{realm}/{_OPENID_PATH}/auth',
        'config.service_logout_url': f'{_KC_REALMS}/{realm}/{_OPENID_PATH}/logout',
        'config.token_url': f'{_KC_REALMS}/{realm}/{_OPENID_PATH}/token',
        'config.user_url': f'{_KC_REALMS}/{realm}/{_OPENID_PATH}/userinfo',
        'config.realm': realm,
    }


def _fill_template(template_str, replacements):
    # take only the required values for formatting
    swaps = {
        k: v
        for k, v in replacements.items()
        if ('{%s}' % k) in template_str
    }
    return template_str.format(**swaps)


def _delete_service(name, routes_fn=None):
    logger.info(f'\nRemoving service "{name}"...')

    try:
        service_info = request(method='get', url=f'{KONG_INTERNAL_URL}/services/{name}')
        service_id = service_info['id']

        # first remove all linked routes
        next_url = f'{KONG_INTERNAL_URL}/services/{name}/routes'
        while next_url:
            res = request(method='get', url=next_url)
            next_url = res['next']

            for route in res['data']:
                route_id = route['id']
                route_name = route['name']

                # check if the route fits the condition to be removed
                if not routes_fn or routes_fn(route):
                    try:
                        request(method='delete', url=f'{KONG_INTERNAL_URL}/routes/{route_id}')
                        logger.success(f'Removed route "{route_name}" ({route_id})')
                    except HTTPError:
                        logger.warning(f'Could not remove route "{route_name}"')

        request(method='delete', url=f'{KONG_INTERNAL_URL}/services/{service_id}')
        logger.success(f'Removed service "{name}"')

    except HTTPError:
        logger.critical(f'Could not remove service "{name}"')


def add_app(name, url):
    logger.info(f'\nExposing service "{name}" at {url}...')

    try:
        # Register service in Kong
        data = {
            'name': name,
            'url': url,
        }
        service_info = request(method='post', url=f'{KONG_INTERNAL_URL}/services/', data=data)
        service_id = service_info['id']
        logger.success(f'Added service "{name}": {service_id}')

        # ADD CORS Plugin to Kong for whole domain CORS
        PLUGIN_URL = f'{KONG_INTERNAL_URL}/services/{name}/plugins'

        config = load_json_file(TEMPLATES['cors'])
        config['config.origins'] = f'{BASE_HOST}/*'
        request(method='post', url=PLUGIN_URL, data=config)

        # Routes
        # Add a route which we will NOT protect
        ROUTE_URL = f'{KONG_INTERNAL_URL}/services/{name}/routes'
        data_route = {
            'name': name,
            'hosts': [BASE_DOMAIN, ],
            'preserve_host': 'true',
            'paths': [f'/{name}', ],
            'strip_path': 'false',
        }
        request(method='post', url=ROUTE_URL, data=data_route)
        logger.success(f'Route  {url}  now being served by kong at  {BASE_HOST}/{name}')

    except Exception as e:
        logger.critical(f'Could not add service "{name}" in kong')
        logger.error(str(e))
        sys.exit(1)


def remove_app(name):
    _delete_service(name)


def add_service(service_config, realm, oidc_client):
    name = service_config['name']  # service name
    host = service_config['host']  # service host

    logger.info(f'\nExposing service "{name}" at {host} for realm "{realm}"...')

    # OIDC plugin settings (same for all OIDC endpoints)
    oidc_data = {}
    if service_config.get(f'{EPT_OIDC}_endpoints'):
        if not oidc_client:
            logger.critical('Cannot execute command without OIDC client')
            sys.exit(1)
        oidc_data = _get_service_oidc_payload(name, realm, oidc_client)

    for ep_type in ENDPOINT_TYPES:
        logger.info(f'Adding {ep_type} endpoints...')

        endpoints = service_config.get(f'{ep_type}_endpoints', [])
        for ep in endpoints:
            context = dict({'realm': realm}, **ep)
            ep_name = ep['name']
            ep_url = _fill_template(ep.get('url'), context)
            service_name = f'{name}_{ep_type}_{ep_name}'
            data = {
                'name': service_name,
                'url': f'{host}{ep_url}',
            }
            try:
                service_info = request(method='post', url=f'{KONG_INTERNAL_URL}/services/', data=data)
                service_id = service_info['id']
                logger.success(f'Added endpoint "{ep_name}": {service_id}')
            except HTTPError:
                logger.warning(f'Could not add endpoint "{ep_name}"')

            ROUTE_URL = f'{KONG_INTERNAL_URL}/services/{service_name}/routes'
            if ep.get('template_path'):
                path = _fill_template(ep.get('template_path'), context)
            else:
                path = ep.get('route_path') or f'/{realm}/{name}{ep_url}'

            route_data = {
                'name': f'{service_name}__{realm}',
                'hosts': [BASE_DOMAIN, ],
                'preserve_host': 'true',
                'paths': [path, ],
                'strip_path': ep.get('strip_path', 'false'),
            }

            try:
                route_info = request(method='post', url=ROUTE_URL, data=route_data)
                logger.success(f'Route  {host}{ep_url}  now being served by kong at  {BASE_HOST}{path}')

                # OIDC routes are protected using the "kong-oidc-auth" plugin
                if ep_type == EPT_OIDC:
                    protected_route_id = route_info['id']
                    _oidc_config = {}
                    _oidc_config.update(oidc_data)
                    _oidc_config.update(ep.get('oidc_override', {}))
                    request(
                        method='post',
                        url=f'{KONG_INTERNAL_URL}/routes/{protected_route_id}/plugins',
                        data=_oidc_config,
                    )

            except HTTPError:
                logger.error(f'Could not add route {host}{ep_url}')

    logger.success(f'Service "{name}" now being served by kong for realm "{realm}"')


def remove_service(service_config, realm):

    def _realm_in_route(route):
        if route['name']:
            return route['name'].endswith(f'__{realm}')
        return any([path.strip('/').startswith(realm) for path in route['paths']])

    name = service_config['name']  # service name
    purge = bool(realm)  # remove service in ALL realms
    routes_fn = None if purge else _realm_in_route

    if purge:
        logger.info(f'\nRemoving service "{name}" from ALL realms...')
    else:
        logger.info(f'\nRemoving service "{name}" from realm "{realm}"...')

    for ep_type in ENDPOINT_TYPES:
        logger.info(f'Removing {ep_type} services...')

        endpoints = service_config.get(f'{ep_type}_endpoints', [])
        for ep in endpoints:
            ep_name = ep['name']
            service_name = f'{name}_{ep_type}_{ep_name}'

            _delete_service(service_name, routes_fn)


def load_definitions(def_path):
    definitions = {}
    _files = [f for f in os.listdir(def_path) if fnmatch.fnmatch(f, '*.json')]

    for f in _files:
        config = load_json_file(f'{def_path}/{f}')
        name = config['name']
        definitions[name] = config
    return definitions


def handle_app(action, name, url=None):
    if action == 'ADD' and not url:
        logger.critical('Cannot execute command without URL')
        sys.exit(1)

    if action == 'ADD':
        add_app(name, url)

    elif action == 'REMOVE':
        remove_app(name)


def handle_service(action, name, realm=None, oidc_client=None):
    if name not in SERVICE_DEFINITIONS:
        logger.critical(f'No service definition for name: "{name}"')
        sys.exit(1)

    service_config = SERVICE_DEFINITIONS[name]

    if action == 'ADD':
        if not realm:
            logger.critical('Cannot execute command without realm')
            sys.exit(1)
        add_service(service_config, realm, oidc_client)

    elif action == 'REMOVE':
        if realm == '*':
            realm = None
        remove_service(service_config, realm)


def handle_solution(action, name, realm=None, oidc_client=None):
    if name not in SOLUTION_DEFINITIONS:
        logger.critical(f'No solution definition for name: "{name}"')
        sys.exit(1)

    if action == 'ADD':
        if not realm:
            logger.critical('Cannot execute command without realm')
            sys.exit(1)
        logger.info(f'\nAdding solution "{name}" for realm "{realm}" in kong...')

    elif action == 'REMOVE':
        if realm == '*':
            realm = None
        if not realm:
            logger.info(f'\nRemoving solution "{name}" from ALL realms in kong...')
        else:
            logger.info(f'\nRemoving solution "{name}" from realm "{realm}" in kong...')

    services = SOLUTION_DEFINITIONS[name].get('services', [])
    for service in services:
        handle_service(action, service, realm, oidc_client)


if __name__ == '__main__':
    logger = get_logger('Kong')

    COMMANDS: Dict[str, Callable] = {
        'APP': handle_app,
        'SERVICE': handle_service,
        'SOLUTION': handle_solution,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        logger.critical(f'No command: {command}')
        sys.exit(1)

    SERVICE_DEFINITIONS = load_definitions(SERVICES_PATH)
    SOLUTION_DEFINITIONS = load_definitions(SOLUTIONS_PATH)

    fn = COMMANDS[command]
    args = sys.argv[2:]
    fn(*args)

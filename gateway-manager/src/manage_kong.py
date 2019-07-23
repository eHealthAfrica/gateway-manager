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

import sys

from typing import Callable, Dict

from requests.exceptions import HTTPError

from manage_keycloak import get_client_secret
from helpers import (
    do_nothing,
    fill_template,
    get_logger,
    load_json_file,
    request,
)
from settings import (
    BASE_HOST,
    BASE_DOMAIN,
    BASE_USE_SSL,

    KONG_INTERNAL_URL,
    KONG_PUBLIC_REALM,

    APPS_PATH,
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

    return load_json_file(TEMPLATES['oidc'], {
        'host': BASE_HOST,
        'domain': BASE_DOMAIN,
        'use_ssl': str(BASE_USE_SSL).lower(),
        'realm': realm,
        'oidc_client_id': client_id,
        'oidc_client_secret': client_secret,
        'service': service_name,
    })


def _check_realm_in_action(action, realm):
    if action == 'ADD':
        if not realm:
            logger.critical('Cannot execute command without realm')
            sys.exit(1)

    elif action == 'REMOVE':
        if realm == '*':
            realm = None

    return realm


def _check_404(url):
    try:
        request(method='get', url=url)
        return False
    except HTTPError as he:
        if he.response.status_code != 404:
            raise he
        return True


def _add_service(config):
    name = config['name']  # service name
    host = config['host']  # service host

    logger.info(f'Exposing service "{name}" at {host}...')

    try:
        if not _check_404(f'{KONG_INTERNAL_URL}/services/{name}'):
            logger.warning(f'Service "{name}" already exists!')
            return

        # Register service
        data = {
            'name': name,
            'url': host,
        }
        service_info = request(method='post', url=f'{KONG_INTERNAL_URL}/services/', data=data)
        service_id = service_info['id']
        logger.success(f'Added service "{name}": {service_id}')

        # ADD CORS Plugin to Kong for whole domain CORS
        config = load_json_file(TEMPLATES['cors'], {'host': BASE_HOST})
        PLUGIN_URL = f'{KONG_INTERNAL_URL}/services/{name}/plugins'
        request(method='post', url=PLUGIN_URL, data=config)
        logger.success(f'Added CORS plugin to service "{name}"')

    except Exception as e:
        logger.critical(f'Could not add service "{name}"')
        raise e


def _remove_service_and_routes(name, routes_fn=None):
    logger.info(f'Removing service "{name}"...')

    if _check_404(f'{KONG_INTERNAL_URL}/services/{name}'):
        logger.warning(f'Service "{name}" does not exist!')
        return

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


def add_app(app_config):
    # Register app as service
    _add_service(app_config)

    name = app_config['name']  # app name

    # Add a public route
    paths = app_config.get('paths', [f'/{name}'])
    if paths:
        # check route
        if not _check_404(f'{KONG_INTERNAL_URL}/services/{name}/routes/{name}'):
            logger.warning(f'Route "{name}" for service "{name}" already exists!')
            return

        data_route = {
            'name': name,
            'hosts': [BASE_DOMAIN, ],
            'preserve_host': 'true',
            'paths': paths,
            'strip_path': 'false',
        }

        ROUTE_URL = f'{KONG_INTERNAL_URL}/services/{name}/routes'
        request(method='post', url=ROUTE_URL, data=data_route)
        logger.success(f'Route paths {paths} now being served at {BASE_HOST}')


def add_service(service_config, realm, oidc_client):
    # Register service
    _add_service(service_config)

    name = service_config['name']  # service name

    logger.info(f'Exposing service "{name}" routes for realm "{realm}"...')
    ROUTE_URL = f'{KONG_INTERNAL_URL}/services/{name}/routes'

    # OIDC plugin settings (same for all OIDC endpoints)
    oidc_data = {}
    if service_config.get(f'{EPT_OIDC}_endpoints'):
        if not oidc_client:
            logger.critical('Cannot execute command without OIDC client')
            sys.exit(1)
        oidc_data = _get_service_oidc_payload(name, realm, oidc_client)

    for ep_type in ENDPOINT_TYPES:
        logger.info(f'Adding {ep_type} endpoints...')

        context = {
            'realm': realm,
            'name': name,
        }
        if ep_type != EPT_OIDC:  # not available in protected routes
            context['public_realm'] = KONG_PUBLIC_REALM

        endpoints = service_config.get(f'{ep_type}_endpoints', [])
        for ep in endpoints:
            ep_name = ep['name']
            route_name = f'{name}__{ep_type}__{ep_name}__{realm}'

            # check route
            if not _check_404(f'{KONG_INTERNAL_URL}/services/{name}/routes/{route_name}'):
                logger.warning(f'Route "{route_name}" for service "{name}" already exists!')
                continue

            paths = [fill_template(p, context) for p in ep.get('paths')]

            route_data = {
                'name': route_name,
                'hosts': [BASE_DOMAIN, ],
                'preserve_host': 'true',
                'paths': paths,
                'strip_path': ep.get('strip_path', 'false'),
                'regex_priority': ep.get('regex_priority', 0),
                'tags': [realm, ]  # use tags to identify assigned realm
            }

            try:
                route_info = request(method='post', url=ROUTE_URL, data=route_data)
                logger.success(f'Route paths {paths} now being served at {BASE_HOST}')

                # OIDC routes are protected using the "Kong-oidc-auth" plugin
                if ep_type == EPT_OIDC:
                    protected_route_id = route_info['id']
                    _oidc_config = {}
                    _oidc_config.update(oidc_data)
                    _oidc_config.update(ep.get('oidc_override', {}))

                    try:
                        request(
                            method='post',
                            url=f'{KONG_INTERNAL_URL}/routes/{protected_route_id}/plugins',
                            data=_oidc_config,
                        )
                        logger.success(f'Route paths {paths} now being protected')
                    except HTTPError:
                        logger.error(f'Could not protect route {paths}')

            except HTTPError:
                logger.error(f'Could not add route paths {paths}')

    logger.success(f'Service "{name}" routes now being served and protected for realm "{realm}"')


def remove_service(name, realm):

    def _realm_in_route(route):
        return realm in route.get('tags', []) or route['name'].endswith(f'__{realm}')

    if not realm:
        logger.info(f'Removing service "{name}" from ALL realms...')
    else:
        logger.info(f'Removing service "{name}" from realm "{realm}"...')

    routes_fn = None if not realm else _realm_in_route
    _remove_service_and_routes(name, routes_fn)


def handle_app(action, name):
    try:
        app_config = load_json_file(f'{APPS_PATH}/{name}.json')
    except Exception:
        logger.critical(f'No app definition for name: "{name}"')
        sys.exit(1)

    if action == 'ADD':
        add_app(app_config)

    elif action == 'REMOVE':
        service_name = app_config['name']
        _remove_service_and_routes(service_name)


def handle_service(action, name, realm=None, oidc_client=None):
    try:
        service_config = load_json_file(f'{SERVICES_PATH}/{name}.json')
    except Exception:
        logger.critical(f'No service definition for name: "{name}"')
        sys.exit(1)

    realm = _check_realm_in_action(action, realm)

    if action == 'ADD':
        add_service(service_config, realm, oidc_client)

    elif action == 'REMOVE':
        service_name = service_config['name']
        remove_service(service_name, realm)


def handle_solution(action, name, realm=None, oidc_client=None):
    try:
        services = load_json_file(f'{SOLUTIONS_PATH}/{name}.json').get('services', [])
    except Exception:
        logger.critical(f'No solution definition for name: "{name}"')
        sys.exit(1)

    realm = _check_realm_in_action(action, realm)

    if action == 'ADD':
        logger.info(f'Adding solution "{name}" for realm "{realm}"...')

    elif action == 'REMOVE':
        if not realm:
            logger.info(f'Removing solution "{name}" from ALL realms...')
        else:
            logger.info(f'Removing solution "{name}" from realm "{realm}"...')

    for service in services:
        handle_service(action, service, realm, oidc_client)


def is_kong_ready():
    try:
        request(method='get', url=KONG_INTERNAL_URL)
        logger.success('Kong is ready!')
    except Exception as e:
        logger.critical('Kong is NOT ready!')
        raise e


if __name__ == '__main__':
    logger = get_logger('Kong')

    COMMANDS: Dict[str, Callable] = {
        'READY': do_nothing,
        'APP': handle_app,
        'SERVICE': handle_service,
        'SOLUTION': handle_solution,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        logger.critical(f'No command: {command}')
        sys.exit(1)

    try:
        is_kong_ready()

        fn = COMMANDS[command]
        args = sys.argv[2:]
        fn(*args)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

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

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

from settings import (
    BASE_HOST,
    KC_URL,
    KC_ADMIN_USER,
    KC_ADMIN_PASSWORD,
    KC_MASTER_REALM,
    KEYCLOAK_AETHER_CLIENT,
    KEYCLOAK_KONG_CLIENT,
    PUBLIC_REALM,
    LOGIN_THEME
)


def client():
    # connect to master realm
    try:
        keycloak_admin = KeycloakAdmin(server_url=KC_URL,
                                       username=KC_ADMIN_USER,
                                       password=KC_ADMIN_PASSWORD,
                                       realm_name=KC_MASTER_REALM,
                                       )
        return keycloak_admin
    except KeycloakError as ke:
        raise RuntimeError(f'Could not get info from keycloak  {str(ke)}')


def client_for_realm(realm):
    keycloak_admin = client()
    try:
        keycloak_admin.realm_name = realm
        return keycloak_admin
    except Exception as e:
        raise RuntimeError(
            f'Unexpected error, do the realm and the client exist?  {str(e)}'
        )


def create_realm(realm, description=None):
    # There is no method for realm creation in KeycloakAdmin!
    print(f'\nAdding realm "{realm}" to keycloak')
    keycloak_admin = client()
    desc = description if description else realm
    config = {
        'realm': realm,
        'displayName': desc,
        'enabled': True,
        'roles': {
            'realm': [
                {
                    'name': 'user',
                    'description': 'User privileges'
                },
                {
                    'name': 'admin',
                    'description': 'Administrative privileges'
                }
            ]
        }
    }
    if LOGIN_THEME:
        config['loginTheme'] = LOGIN_THEME
    keycloak_admin.create_realm(config, skip_exists=True)
    print(f'    + Added realm {realm} >> keycloak')
    return


def create_client(realm, config):
    keycloak_admin = client_for_realm(realm)
    keycloak_admin.create_client(config, skip_exists=True)


def create_aether_client(realm):

    print(f'Creating aether client in realm [{realm}]...')
    REALM_URL = f'{BASE_HOST}/{realm}/'
    PUBLIC_URL = f'{BASE_HOST}/{PUBLIC_REALM}/*'

    config = {
        'clientId': KEYCLOAK_AETHER_CLIENT,
        'publicClient': True,  # allow users to get a token for auth
        'clientAuthenticatorType': 'client-secret',
        'directAccessGrantsEnabled': True,
        'baseUrl': REALM_URL,
        'redirectUris': [
            '*',
            PUBLIC_URL
        ],
        'enabled': True,
        'protocolMappers': [
            {
                'name': 'groups',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-realm-role-mapper',
                'consentRequired': False,
                'config': {
                    'multivalued': True,
                    'userinfo.token.claim': True,
                    'user.attribute': 'foo',
                    'id.token.claim': True,
                    'access.token.claim': True,
                    'claim.name': 'groups',
                    'jsonType.label': 'String'
                }
            }
        ]
    }
    create_client(realm, config)


def create_oidc_client(realm):

    print(f'Creating client [{KEYCLOAK_KONG_CLIENT}] in realm [{realm}]...')
    REALM_URL = f'{BASE_HOST}/{realm}/'

    config = {
        'clientId': KEYCLOAK_KONG_CLIENT,
        'publicClient': False,
        'clientAuthenticatorType': 'client-secret',
        'directAccessGrantsEnabled': True,
        'baseUrl': REALM_URL,
        'redirectUris': [
            '*'
        ],
        'enabled': True,
        'protocolMappers': [
            {
                'name': 'groups',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-realm-role-mapper',
                'consentRequired': False,
                'config': {
                    'multivalued': True,
                    'userinfo.token.claim': True,
                    'user.attribute': 'foo',
                    'id.token.claim': True,
                    'access.token.claim': True,
                    'claim.name': 'groups',
                    'jsonType.label': 'String'
                }
            }
        ]
    }
    create_client(realm, config)


def create_user(
    realm,
    user,
    password=None,
    admin=False,
    email=None,
    temporary_password=False
):
    print(f'\nAdding user "{user}" to {realm}')
    # clean command line inputs
    if not isinstance(admin, bool):
        admin = bool(admin)
    if not isinstance(temporary_password, bool):
        temporary_password = bool(temporary_password)

    realm_roles = ['admin', 'user', ] if admin else ['user', ]
    config = {
        'username': user,
        'enabled': True,
        'realmRoles': realm_roles,
        'email': email
    }
    keycloak_admin = client_for_realm(realm)
    keycloak_admin.create_user(config)
    if password:
        user_id = keycloak_admin.get_user_id(username=user)
        keycloak_admin.set_user_password(
            user_id,
            password,
            temporary=temporary_password
        )
    print(f'    + Added user {user} >> {realm}')


def keycloak_ready():
    try:
        client()
        print(f'Keycloak is ready.')
    except RuntimeError:
        sys.exit(1)


if __name__ == '__main__':
    commands: Dict[str, Callable] = {
        'ADD_REALM': create_realm,
        'ADD_USER': create_user,
        'ADD_AETHER_CLIENT': create_aether_client,
        'ADD_OIDC_CLIENT': create_oidc_client,
        'KEYCLOAK_READY': keycloak_ready
    }
    command = sys.argv[1]
    args = sys.argv[2:]
    if command.upper() not in commands.keys():
        raise KeyError(f'No command: {command}')
    fn = commands[command]
    fn(*args)

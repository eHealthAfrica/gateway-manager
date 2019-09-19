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

from helpers import (
    do_nothing,
    get_logger,
    load_json_file,
)

from settings import (
    BASE_HOST,
    KC_ADMIN_URL,
    KC_ADMIN_USER,
    KC_ADMIN_PASSWORD,
    KC_ADMIN_REALM,
    KONG_PUBLIC_REALM,
    TEMPLATES,
)

LOGGER = get_logger('Keycloak')


############################################
#
# Keycloak Admin helpers
#
############################################

def get_client():
    try:
        # connect to master realm
        keycloak_admin = KeycloakAdmin(server_url=KC_ADMIN_URL,
                                       username=KC_ADMIN_USER,
                                       password=KC_ADMIN_PASSWORD,
                                       realm_name=KC_ADMIN_REALM,
                                       )
        return keycloak_admin

    except KeycloakError as ke:
        LOGGER.critical('Keycloak is NOT ready!')
        LOGGER.error(str(ke))
        sys.exit(1)


def client_for_realm(realm):
    try:
        keycloak_admin = get_client()
        keycloak_admin.realm_name = realm
        keycloak_admin.users_count()  # check that realm exists
        return keycloak_admin

    except Exception as e:
        LOGGER.warning(f'Do the realm "{realm}" exist?')
        LOGGER.error(str(e))
        sys.exit(1)


def get_client_secret(realm, client_id):
    try:
        keycloak_admin = client_for_realm(realm)
        client_pk = keycloak_admin.get_client_id(client_id)
        secrets = keycloak_admin.get_client_secrets(client_pk)
        return secrets.get('value')

    except KeycloakError as ke:
        LOGGER.error('Could not get info from Keycloak')
        LOGGER.error(str(ke))
        sys.exit(1)
    except Exception as e:
        LOGGER.warning(f'Do the realm "{realm}" and the client "{client_id}" exist?')
        LOGGER.error(str(e))
        sys.exit(1)


def is_keycloak_ready():
    get_client()
    LOGGER.success('Keycloak is ready!')


def get_user(realm, username):
    keycloak_admin = client_for_realm(realm)
    user_id = keycloak_admin.get_user_id(username)
    return keycloak_admin.get_user(user_id)


def get_realm_roles(realm):
    keycloak_admin = client_for_realm(realm)
    realm_roles = keycloak_admin.get_realm_roles()
    return realm_roles


def get_clients(realm, name=None):
    keycloak_admin = client_for_realm(realm)
    clients = keycloak_admin.get_clients()
    if not name:
        return clients
    try:
        return [i for i in clients if i.get('clientId') == name][0]
    except IndexError:
        return None


def get_client_roles(realm, client_id):
    keycloak_admin = client_for_realm(realm)
    client_roles = keycloak_admin.get_client_roles(client_id=client_id)
    return client_roles


############################################
#
# Keycloak Actions
#
############################################

def assign_all_client_roles(realm, username, client_name):
    keycloak_admin = client_for_realm(realm)
    user = get_user(realm, username)
    client = get_clients(realm, client_name)
    client_roles = get_client_roles(realm, client.get('id'))
    roles = [
        {'id': role.get('id'), 'name': role.get('name')}
        for role in client_roles
    ]
    keycloak_admin.assign_client_role(
        client_id=client.get('id'),
        user_id=user.get('id'),
        roles=roles
    )
    LOGGER.success(f'Added all rights to client "{client_name}"'
                   f' to "{username}" on realm "{realm}"')


def create_realm(realm, description=None, login_theme=None):
    LOGGER.info(f'Adding realm "{realm}"...')
    keycloak_admin = get_client()

    config = load_json_file(TEMPLATES['realm'], {
        'realm': realm,
        'displayName': description or '',
        'loginTheme': login_theme or '',
    })
    if not description:
        config['displayName'] = None
    if not login_theme:
        config['loginTheme'] = None

    _status = keycloak_admin.create_realm(config, skip_exists=True)
    if _status:
        LOGGER.warning(f'- {str(_status)}')
    LOGGER.success(f'Added realm "{realm}"')


def create_user(
    realm,
    user,
    password=None,
    admin=False,
    email=None,
    temporary_password=False,
):
    LOGGER.info(f'Adding user "{user}" to realm "{realm}"...')

    user_type = 'admin' if bool(admin) else 'standard'
    config = load_json_file(TEMPLATES['user'][user_type], {
        'username': user,
        'email': email or '',
    })
    if not email:
        config['email'] = None

    keycloak_admin = client_for_realm(realm)

    _user_id = keycloak_admin.get_user_id(username=user)
    if _user_id:
        _status = keycloak_admin.update_user(_user_id, config)
    else:
        _status = keycloak_admin.create_user(config)

    if _status:
        LOGGER.warning(f'- {str(_status)}')

    if password:
        user_id = keycloak_admin.get_user_id(username=user)
        _status_pwd = keycloak_admin.set_user_password(
            user_id,
            password,
            temporary=bool(temporary_password),
        )
        if _status_pwd:
            LOGGER.warning(f'- {str(_status_pwd)}')
    LOGGER.success(f'Added user "{user}" to realm "{realm}"')
    if admin:
        LOGGER.info(f'Granting user "{user}" admin rights on realm "{realm}"...')
        assign_all_client_roles(realm, user, 'realm-management')


def create_confidential_client(realm, name):
    LOGGER.info(f'Adding confidential client "{name}" to realm "{realm}"...')
    create_client(realm, name, False)


def create_public_client(realm, name):
    LOGGER.info(f'Adding public client "{name}" to realm "{realm}"...')
    create_client(realm, name, True)


def create_client(realm, name, isPublic):
    config = load_json_file(TEMPLATES['client'], {
        'name': name,
        'host': BASE_HOST,
        'realm': realm,
        'publicRealm': KONG_PUBLIC_REALM,
    })
    if not isPublic:
        config['publicClient'] = False
        config['redirectUris'] = ['*']

    keycloak_admin = client_for_realm(realm)
    _status = keycloak_admin.create_client(config, skip_exists=True)
    if _status:
        LOGGER.warning(f'- {str(_status)}')
    LOGGER.success(f'Added client "{name}" to realm "{realm}"')


if __name__ == '__main__':
    COMMANDS: Dict[str, Callable] = {
        'READY': do_nothing,
        'ADD_REALM': create_realm,
        'ADD_USER': create_user,
        'ADD_CONFIDENTIAL_CLIENT': create_confidential_client,
        'ADD_PUBLIC_CLIENT': create_public_client,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    is_keycloak_ready()

    fn = COMMANDS[command]
    args = sys.argv[2:]
    fn(*args)

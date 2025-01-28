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
    categorize_arguments,
    check_realm,
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

def get_client(exit_on_error=True):
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
        if exit_on_error:
            sys.exit(1)
        raise ke


def client_for_realm(realm, exit_on_error=True):
    try:
        keycloak_admin = get_client(exit_on_error)
        # sometimes authentication fails, this is due to some internal caching
        # clear the internal caching first
        keycloak_admin.clear_realm_cache()
        keycloak_admin.change_current_realm(realm)
        # keycloak_admin.users_count()  # check that realm exists
        return keycloak_admin

    except Exception as e:
        LOGGER.warning(f'Do the realm "{realm}" exist?')
        LOGGER.error(str(e))
        if exit_on_error:
            sys.exit(1)
        raise e


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


def get_realm_display_name(realm):
    try:
        keycloak_admin = client_for_realm(realm, exit_on_error=False)
        # get all realms and search for current one
        realms = keycloak_admin.get_realms()
        for r in realms:
            if r['realm'] == realm:
                return r.get('displayNameHtml') or r.get('displayName') or realm
        return realm
    except Exception:
        return realm


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


def assign_all_client_roles(realm, username, client_name):
    check_realm(realm)

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
        roles=roles,
    )
    LOGGER.success(f'Added all rights to client "{client_name}"'
                   f' to "{username}" on realm "{realm}"')


############################################
#
# Keycloak Actions
#
############################################


def create_realm(realm, *args, kwargs={}):
    check_realm(realm)

    config = load_json_file(TEMPLATES['realm'], {
        'realm': realm,
        'displayName': kwargs.get('description', realm),
        'accountTheme': kwargs.get('account_theme', 'keycloak'),
        'adminTheme': kwargs.get('admin_theme', 'keycloak'),
        'emailTheme': kwargs.get('email_theme', 'keycloak'),
        'loginTheme': kwargs.get('login_theme', 'keycloak'),
        'host': BASE_HOST,
        'publicRealm': KONG_PUBLIC_REALM,
    })

    if kwargs.get('test'):
        LOGGER.debug(config)
        return

    LOGGER.info(f'Adding realm "{realm}"...')
    keycloak_admin = get_client()

    _status = keycloak_admin.create_realm(config, skip_exists=True)
    if _status:
        LOGGER.warning(f'- {str(_status)}')
    LOGGER.success(f'Added realm "{realm}"')


def create_admin(realm, username, password=None, temporary_password=False, *args, kwargs={}):
    create_user(realm, username, password, temporary_password, *args, kwargs)

    if kwargs.get('test'):
        return

    LOGGER.info(f'Granting user "{username}" admin rights on realm "{realm}"...')
    assign_all_client_roles(realm, username, 'realm-management')


def create_user(realm, username, password=None, temporary_password=False, *args, kwargs={}):
    check_realm(realm)

    config = {'username': username, 'enabled': True}
    if kwargs.get('test'):
        LOGGER.debug(config)
        return

    LOGGER.info(f'Adding/Updating user "{username}" to realm "{realm}"...')
    keycloak_admin = client_for_realm(realm)

    _user_id = keycloak_admin.get_user_id(username=username)
    if _user_id:
        _status = keycloak_admin.update_user(_user_id, config)
    else:
        _status = keycloak_admin.create_user(config)
    if _status:
        LOGGER.warning(f'- {str(_status)}')

    if password:
        user_id = keycloak_admin.get_user_id(username=username)
        _status_pwd = keycloak_admin.set_user_password(
            user_id=user_id,
            password=password,
            temporary=bool(temporary_password),
        )
        if _status_pwd:
            LOGGER.warning(f'- {str(_status_pwd)}')

    if _user_id:
        LOGGER.success(f'Updated user "{username}" on realm "{realm}"')
    else:
        LOGGER.success(f'Added user "{username}" to realm "{realm}"')


def add_user_group(realm, username, group, *args, kwargs={}):
    check_realm(realm)

    if kwargs.get('test'):
        return

    LOGGER.info(f'Adding user "{username}" to group "{group}" on realm "{realm}"...')
    keycloak_admin = client_for_realm(realm)
    user_id = keycloak_admin.get_user_id(username=username)
    groups = keycloak_admin.get_groups()  # get all groups
    was_added = False
    for g in groups:
        if g['name'] == group:  # identify group by name
            keycloak_admin.group_user_add(user_id=user_id, group_id=g['id'])
            LOGGER.success(f'Added user "{username}" to group "{group}" on realm "{realm}"')
            was_added = True
    if not was_added:
        LOGGER.warning(f'Could not add user "{username}" to group "{group}" on realm "{realm}"')


def create_confidential_client(realm, name, *args, kwargs={}):
    check_realm(realm)

    LOGGER.info(f'Adding confidential client "{name}" to realm "{realm}"...')
    create_client(realm, name, False, *args, kwargs)


def create_public_client(realm, name, *args, kwargs={}):
    check_realm(realm)

    LOGGER.info(f'Adding public client "{name}" to realm "{realm}"...')
    create_client(realm, name, True, *args, kwargs)


def create_client(realm, name, isPublic, *args, kwargs={}):
    check_realm(realm)

    config = load_json_file(TEMPLATES['client'], {
        'name': name,
        'host': BASE_HOST,
        'realm': realm,
        'publicRealm': KONG_PUBLIC_REALM,
    })
    if not isPublic:
        config['publicClient'] = False
        config['redirectUris'] = ['*']

    if kwargs.get('login_theme'):
        config['attributes'] = config.get('attributes', {})
        config['attributes']['login_theme'] = kwargs['login_theme']

    if kwargs.get('test'):
        LOGGER.debug(config)
        return

    keycloak_admin = client_for_realm(realm)
    _status = keycloak_admin.create_client(config, skip_exists=True)
    if _status:
        LOGGER.warning(f'- {str(_status)}')
    LOGGER.success(f'Added client "{name}" to realm "{realm}"')


if __name__ == '__main__':
    COMMANDS: Dict[str, Callable] = {
        'READY': do_nothing,
        'ADD_REALM': create_realm,
        'ADD_ADMIN': create_admin,
        'ADD_USER': create_user,
        'ADD_USER_GROUP': add_user_group,
        'ADD_CONFIDENTIAL_CLIENT': create_confidential_client,
        'ADD_PUBLIC_CLIENT': create_public_client,
    }

    args, kwargs = categorize_arguments(sys.argv[:])
    command = args[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    try:
        if not kwargs.get('test'):
            is_keycloak_ready()

        fn = COMMANDS[command]
        args = args[2:]
        fn(*args, kwargs=kwargs or {})
    except Exception as e:
        LOGGER.error(str(e))
        sys.exit(1)

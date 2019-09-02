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


from dataclasses import dataclass, fields
from datetime import datetime
import re
import sys

import pexpect

import helpers
from settings import (
    CC_CLI_PATH,
    CC_API_USER,
    CC_API_PASSWORD,
    CC_CLUSTER_NAME,
    CC_ENVIRONMENT_NAME
)


LOGGER = helpers.get_logger('ConfluentCloud')


# field order MUST match return order for CCloud
@dataclass
class Environment:
    id: str
    name: str


@dataclass
class Cluster:
    id: str
    name: str
    provider: str
    region: str
    durability: str
    status: str


@dataclass
class ServiceAccount:
    id: int
    name: str
    desc: str


@dataclass
class NewAPIKey:
    name: str
    key: str


@dataclass
class APIKey:
    id: str
    service_account_id: int
    desc: str


@dataclass
class ACL:
    id: int  # ID of ServiceAccount
    permission: str
    operation: str
    resource_class: str
    resource_id: str
    acl_type: str


#####################################
#
#   Access
#
#####################################

def login(user, pw):
    login_prompt = 'Email:*'
    pw_prompt = 'Password:*'
    child = pexpect.spawn(f'{CC_CLI_PATH} login --url https://confluent.cloud')
    child.expect(login_prompt)
    child.sendline(user)
    child.expect(pw_prompt)
    child.sendline(pw)
    res = child.read().decode("utf-8")
    if 'Logged in' not in res:
        raise ConnectionError(f'Login Failed: {_inline(res)}')
    LOGGER.debug(_inline(res))
    return True


def logout():
    child = pexpect.spawn(f'{CC_CLI_PATH} logout')
    res = child.read().decode("utf-8")
    if 'You are now logged out' not in res:
        raise LOGGER.error(f'Could not disconnect: {_inline(res)}')
    LOGGER.debug(_inline(res))
    return True


#####################################
#
#   Environments
#
#####################################


def _handle_env(i):
    # removes the currently selected indicator (*) from the name
    i['id'] = i['id'].replace('*', '').strip()
    return i


def list_environments():
    LOGGER.debug('Fetching environments...')
    child = pexpect.spawn(f'{CC_CLI_PATH} environment list')
    res = str(child.read())
    return _process_resource(Environment, res, _handle_env)


def set_environment(name):
    envs = list_environments()
    match = [e for e in envs if e.name == name]
    if not match:
        raise ValueError(f'No environment named: {name}')
    env = match[0]
    LOGGER.debug(f'Setting environment : {env}')
    child = pexpect.spawn(f'{CC_CLI_PATH} environment use {env.id}')
    res = child.read().decode("utf-8")
    if 'Error: ' in res:
        raise ValueError(f'Could not set env to {env.id}: {_inline(res)}')
    LOGGER.debug(_inline(res))
    return True


#####################################
#
#   Clusters
#
#####################################

def list_clusters():
    LOGGER.debug('Fetching clusters...')
    child = pexpect.spawn(f'{CC_CLI_PATH} kafka cluster list')
    res = str(child.read())
    return _process_resource(Cluster, res)


def set_cluster(name):
    clusters = list_clusters()
    match = [e for e in clusters if e.name == name]
    if not match:
        raise ValueError(f'No cluster named: {name}')
    cluster = match[0]
    LOGGER.debug(f'Setting cluster : {cluster}')
    child = pexpect.spawn(f'{CC_CLI_PATH} kafka cluster use {cluster.id}')
    res = child.read().decode("utf-8")
    if 'Error: ' in res:
        raise ValueError(f'Could not set cluster to {cluster.id}: {_inline(res)}')
    LOGGER.debug(f'Set cluster to {name}')
    return True


#####################################
#
#   Service Accounts
#
#####################################

def get_or_create_tenant_sa(realm):
    accounts = get_service_accounts()
    match = [a for a in accounts if a.name == realm]
    if match:
        LOGGER.info(f'Tenant {realm} already exists!')
        return match[0]
    else:
        create_service_account(realm, f'SA for realm {realm}')
        return _get_service_account_by_name(realm)


def _handle_service_account(i):
    i['id'] = int(i['id'])  # cast to int
    return i


def get_service_accounts():
    LOGGER.debug('Fetching SAs...')
    child = pexpect.spawn(f'{CC_CLI_PATH} service-account list')
    res = str(child.read())
    return _process_resource(ServiceAccount, res, _handle_service_account)


def _get_service_account_by_name(name):
    sas = get_service_accounts()
    match = [sa for sa in sas if sa.name == name]
    if not match:
        sa_names = [sa.name for sa in sas]
        raise ValueError(
            f'No service account found with name: {name}'
            f'. Available SAs: {sa_names}'
        )
    LOGGER.debug(f'Found SA by name: {match[0]}')
    return match[0]


def create_service_account(name: str, desc: str):
    child = pexpect.spawn(f'{CC_CLI_PATH} service-account create "{name}" --description "{desc}"')
    res = child.read().decode("utf-8")
    if 'Error: error creating service account:' in res:
        raise ValueError(f'Account "{name}" not created: {_inline(res)}')
    LOGGER.info(f'ServiceAccount Created for {name}: {desc}')
    return True


def remove_service_account(name: str = None, _id: int = None):
    if not any([_id, name]):
        raise ValueError('You must specify an Account name or ID to remove.')
    if not _id:
        sa = _get_service_account_by_name(name)
        _id = sa.id
    LOGGER.debug(f'Removing SA: {_id}')
    child = pexpect.spawn(f'{CC_CLI_PATH} service-account delete {_id}')
    res = child.read().decode("utf-8")
    if 'Error: ' in res:
        raise ValueError(f'Account "{_id}" not removed: {_inline(res)}')
    LOGGER.info(f'ServiceAccount {_id} removed')
    return True


#####################################
#
#   ACLs
#
#####################################

# See permission spec @
# https://docs.confluent.io/current/kafka/authorization.html#acl-format

ALL_TENANT_PERMISSION = [
    'CREATE',
    'DELETE',
    'DESCRIBE',
    'READ',
    'WRITE'
]


ALL_SU_PERMISSION = ALL_TENANT_PERMISSION[:] + [
    'ALTER',
    'ALTER-CONFIGS',
    'CLUSTER-ACTION',
    'DESCRIBE-CONFIGS',
    'IDEMPOTENT-WRITE'
]


def _handle_acl(i):
    i['id'] = int(i['id'].split(':')[1])  # User:00001 -> 00001
    return i


def acl_create(
    # Have to use ID, no names
    service_account_id: int,
    # the resource
    resource_id=None,
    # OR consumer-group
    resource_type='topic',
    # OR [alter, alter-configs, cluster-action, create, delete, describe,
    # describe-configs, idempotent-write, read, write]
    operation='READ',
    # or deny
    type_='allow',
    # If it's a prefix
    extended_acl=False,
    # Apply to Cluster itself (Add ACLs, etc)
    cluster=False
):
    CMD = ''.join([
        f'{CC_CLI_PATH} kafka acl create --{type_} ',
        f'--service-account-id {service_account_id} ',
        '--prefix ' if extended_acl else '',
        f'--operation {operation} ',
        '--cluster-scope' if cluster else '',
        f'--{resource_type} ' if resource_type else '',
        f"'{resource_id}'" if resource_id else ''  # needs '' around str
    ])
    LOGGER.debug(f'Updating ACL: {CMD}')
    child = pexpect.spawn(CMD)
    res = child.read().decode("utf-8")
    if 'Error: ' in res:
        LOGGER.error(f'ACL not updated: {res}')
        return False
    LOGGER.debug(f'ACL Updated')
    return True


def acl_list(
    # Have to use ID, no names
    service_account_id: int = None,
    # the resource
    resource_id=None,
    # OR consumer-group
    resource_type='topic',
    # If it's a wildcard
    extended_acl=False
):
    CMD = ''.join([
        f'{CC_CLI_PATH} kafka acl list ',
        f'--service-account-id {service_account_id} ' if service_account_id else '',
        '--prefix ' if extended_acl else '',
        f'--{resource_type} {resource_id}' if resource_id else ''
    ])
    child = pexpect.spawn(CMD)
    res = str(child.read())
    return _process_resource(ACL, res, _handle_acl)


#####################################
#
#   APIKeys
#
#####################################

def _handle_api_key(i):
    i['service_account_id'] = int(i['service_account_id'])
    i['desc'] = i['desc'].strip()
    return i


def api_key_create(service_account_id: int, desc: str = None):
    cols = _fields(NewAPIKey)
    parser = _gen_table_parser(cols, NewAPIKey)
    CMD = ''.join([
        f'{CC_CLI_PATH} api-key create ',
        f'--service-account-id {service_account_id}',
        f' --description "{desc}"' if desc else ''
    ])
    child = pexpect.spawn(CMD)
    res = child.read().decode('utf-8')
    return parser(res)


def api_key_list():
    CMD = f'{CC_CLI_PATH} api-key list'
    child = pexpect.spawn(CMD)
    res = str(child.read())
    return _process_resource(APIKey, res, _handle_api_key, True)


#####################################
#
#   Utilities
#
#####################################


# ordered fields in a dataclass
def _fields(cls):
    return [field.name for field in fields(cls)]


def _inline(s: str):
    # removes whitespace and newlines and replaces with single space for logs
    return ' '.join(s.split())


#  results come back to the terminal as | delimited tables
#  generating from column headers ( / class attrs) allows us
#  to return rows by name and use our dataclasses
def _gen_ccloud_regex(columns, debug=False):
    ex = r'\s*(?P<' + columns[0] + r'>.+?(?=\s*\\|))'
    # middle
    for name in columns[1:-1]:
        piece = r'(?:\s*\|\s*)(?P<' + name + r'>.+?(?=\s*\\|))'
        ex += piece
    ex += r'(?:\s*\|\s*)(?P<' + columns[-1] + r'>.+?(?=\s*\\r))'
    if debug:
        LOGGER.debug(ex)
    return re.compile(ex)


def _gen_table_parser(columns, _cls, starting_row=2, debug=False):
    def f(body):
        kwargs = {}
        lines = body.split('\n')
        if debug:
            LOGGER.debug(lines)
        for i, key in enumerate(columns):
            _, header, value, _ = lines[i + starting_row].split('|')
            if debug:
                LOGGER.debug([header, value])
            kwargs[key] = value.strip()
        return _cls(**kwargs)
    return f

# handles the result of a GET request from CCloud using the dataclass
# as the basis for creating a regex and processing the output into
# class instances


def _process_resource(_cls, body, item_handler=helpers.identity, debug=False):
    if debug:
        LOGGER.debug(body)
    cols = _fields(_cls)
    reg = _gen_ccloud_regex(cols, debug)
    if 'Error: ' in body:
        LOGGER.error(f'Could not get {_cls.__name__}s: {body}')
        return False
    lines = body.split('\\n')[1:]
    items = []
    for line in lines:
        match = reg.match(line)
        if not match:
            continue
        # handle overhangs for long fields
        if match.group(cols[0]).strip():
            kwargs = {k: match.group(k) for k in cols}
            kwargs = item_handler(kwargs)
            i = _cls(**kwargs)
            items.append(i)
        else:
            # find items that bled into the next row
            kwargs = {k: match.group(k) for k in cols if match.group(k).strip()}
            for k, val in kwargs.items():
                # stick them onto the ends of the previous values
                old = getattr(items[-1], k)
                old = old + ' ' + val
                setattr(items[-1], k, old)

    for i in items:
        LOGGER.debug(i)
    return items


#####################################
#
#   Commands
#
#####################################

def _connect():
    LOGGER.info('Connecting to CCloud...')
    login(CC_API_USER, CC_API_PASSWORD)
    set_environment(CC_ENVIRONMENT_NAME)
    set_cluster(CC_CLUSTER_NAME)
    LOGGER.info(f'Successfully connected to CCloud: {CC_ENVIRONMENT_NAME} - {CC_CLUSTER_NAME}')


def create_superuser(name):
    _connect()
    account = get_or_create_tenant_sa(name)
    grant_superuser(account=account)
    LOGGER.info(f'Superuser "{name}" created.')


def grant_superuser(name=None, account=None):
    if not any([name, account]):
        raise ValueError('You must specify a name or pass an SA ID.')
    if not account:
        _connect()
        account = _get_service_account_by_name(name)
    allowed_resource = '*'
    for operation in ALL_SU_PERMISSION:
        for resource_type, resource_id, wildcard, cluster in [
                ('topic', allowed_resource, False, False),
                ('consumer-group', allowed_resource, False, False),
                (None, None, False, True)
        ]:
            acl_create(
                account.id,
                resource_id,
                resource_type=resource_type,
                operation=operation,
                extended_acl=wildcard,
                cluster=cluster
            )
    acl_list(service_account_id=account.id)
    logout()


def create_tenant(realm):
    _connect()
    account = get_or_create_tenant_sa(realm)
    allowed_resource = f'{realm}.'
    for operation in ALL_TENANT_PERMISSION:
        for resource_type, resource_id, wildcard in [
                ('topic', allowed_resource, True),
                ('consumer-group', allowed_resource, True)
        ]:
            acl_create(
                account.id,
                resource_id,
                resource_type=resource_type,
                operation=operation,
                extended_acl=wildcard,
                cluster=False
            )
    acl_list(service_account_id=account.id)
    LOGGER.info('Regular tenant "{realm}" created.')
    logout()


def create_key(account_name, desc=None):
    _connect()
    if not desc:
        now = str(datetime.now().isoformat())
        desc = f'Account:{account_name} generated: {now}'
    LOGGER.info(f'Creating key for account: {account_name}')
    account = _get_service_account_by_name(account_name)
    key = api_key_create(account.id, desc)
    LOGGER.info('~~~ SAVE THIS KEY!!! IT CANNOT BE RETRIEVED ~~~')
    LOGGER.info(key)
    logout()


def list_accounts():
    _connect()
    accounts = get_service_accounts()
    for account in accounts:
        LOGGER.info(account)
    logout()


def list_acls(account_name=None):
    _connect()
    sa_id = None
    if account_name:
        account = _get_service_account_by_name(account_name)
        sa_id = account.id
        acls = acl_list(service_account_id=sa_id)
        LOGGER.info(account)
        for acl in acls:
            LOGGER.info(acl)
    else:
        accounts = get_service_accounts()
        acls = acl_list(service_account_id=sa_id)
        for account in accounts:
            LOGGER.info(account)
            for acl in acls:
                if account.id == acl.id:
                    LOGGER.info(acl)

    logout()


def list_api_keys():
    _connect()
    keys = api_key_list()
    for key in keys:
        LOGGER.info(key)
    logout()


if __name__ == '__main__':
    COMMANDS = {
        'ADD_SUPERUSER': create_superuser,
        'GRANT_SUPERUSER': grant_superuser,
        'ADD_TENANT': create_tenant,
        'CREATE_KEY': create_key,
        'LIST_SERVICE_ACCOUNTS': list_accounts,
        'LIST_ACLS': list_acls,
        'LIST_API_KEYS': list_api_keys
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    # try:
    fn = COMMANDS[command]
    args = sys.argv[2:]
    fn(*args)
    # except Exception as e:
    #     LOGGER.error(str(e))
    #     sys.exit(1)

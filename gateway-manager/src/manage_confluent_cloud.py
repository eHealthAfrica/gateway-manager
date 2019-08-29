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
import re
import sys

import pexpect

from helpers import get_logger
from settings import (
    CC_CLI_PATH,
    CC_API_USER,
    CC_API_PASSWORD
)


LOGGER = get_logger('ConfluentCloud')


# field order should match return order for CCloud
@dataclass
class Environment:
    id: str
    name: str


@dataclass
class ServiceAccount:
    id: int
    name: str
    desc: str


@dataclass
class APIKey:
    name: str
    key: str


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


def list_environments():
    LOGGER.debug('Fetching environments...')
    child = pexpect.spawn(f'{CC_CLI_PATH} environment list')
    res = str(child.read())
    lines = res.split('\\n')[1:]
    cols = _fields(Environment)
    reg = gen_ccloud_regex(cols)
    envs = []
    for line in lines:
        match = reg.match(line)
        if not match:
            continue
        kwargs = {k: match.group(k) for k in cols}
        # remove default mark
        kwargs['id'] = kwargs['id'].replace('*', '').strip()
        env = Environment(**kwargs)
        LOGGER.debug(env)
        envs.append(env)
    return envs


def set_environment(name):
    pass


def logout():
    child = pexpect.spawn(f'{CC_CLI_PATH} logout')
    res = child.read().decode("utf-8")
    if 'You are now logged out' not in res:
        raise ConnectionError(f'Could not disconnect: {_inline(res)}')
    LOGGER.debug(_inline(res))
    return True


#####################################
#
#   Service Accounts
#
#####################################

def get_service_accounts():
    accounts = []
    child = pexpect.spawn(f'{CC_CLI_PATH} service-account list')
    # we want to keep the whitespace chars for easy splitting/handling/regex
    lines = str(child.read())
    lines = lines.split('\\n')[1:]  # skip headers
    cols = _fields(ServiceAccount)
    reg = gen_ccloud_regex(cols)
    for line in lines:
        match = reg.match(line)
        if not match:
            continue
        kwargs = {k: match.group(k) for k in cols}
        kwargs['id'] = int(kwargs['id'])  # cast to int
        accounts.append(ServiceAccount(**kwargs))
    return accounts


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
    LOGGER.debug(_inline(res))
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
    LOGGER.debug(f'SA {_id} removed')
    return True


#####################################
#
#   ACLs
#
#####################################

def acl_create(
    # Have to use ID, no names
    service_account_id: int,
    # the resource
    resource_id,
    # OR consumer-group
    resource_type='topic',
    # OR [alter, alter-configs, cluster-action, create, delete, describe,
    # describe-configs, idempotent-write, read, write]
    operation='READ',
    # or deny
    type_='allow',
    # If it's a wildcard
    extended_acl=False
):
    CMD = ''.join([
        f'{CC_CLI_PATH} kafka acl create --{type_} ',
        f'--service-account-id {service_account_id} ',
        '--prefix ' if extended_acl else '',
        f'--operation {operation} '
        f'--{resource_type} ',
        resource_id
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
    LOGGER.debug(f'Getting ACLs: {CMD}')
    child = pexpect.spawn(CMD)
    res = child.read().decode("utf-8")
    if 'Error: ' in res:
        LOGGER.error(f'Could not get ACLs: {res}')
        return False

    LOGGER.debug(f'ACLs: {_inline(res)}')
    return True


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
#  providing a list of column headers allows us to return rows by name
def gen_ccloud_regex(columns):
    ex = r'\s*(?P<' + columns[0] + r'>.+?(?=\s*\\|))'
    # middle
    for name in columns[1:-1]:
        piece = r'(?:\s*\|\s*)(?P<' + name + r'>.+?(?=\s*\\|))'
        ex += piece
    ex += r'(?:\s*\|\s*)(?P<' + columns[-1] + r'>.+?(?=\s*\\r))'
    return re.compile(ex)


#####################################
#
#   Commands
#
#####################################

def create_superuser(name, password):
    '''
    # make user for name
    LOGGER.info(f'Creating SuperUser: {name}')
    make_user(ZOOKEEPER, name, password)
    sleep(ZK_LAG_TIME)
    grant_superuser(name)
    '''
    pass


def grant_superuser(name):
    '''
    for resource_type, resource_id in [
        ('topic', '*'),
        ('group', '*'),
        ('cluster', 'kafka-cluster'),
    ]:
        upsert_permission(
            ZOOKEEPER,
            name,
            resource_id,
            resource_type=resource_type,
            operation='All',
            extended_acl=False
        )
    '''
    pass


def create_tenant(realm):
    '''
        # make user for realm
    LOGGER.info(f'Creating tenant for realm: {realm}')
    pw = get_tenant_password(realm)
    make_user(ZOOKEEPER, realm, pw)
    sleep(ZK_LAG_TIME)
    # give user permission on all realm artifacts in kafka
    allowed_resource = f'{realm}.'
    for resource_type, resource_id, operation, wildcard in [
        ('topic', allowed_resource, 'All', True),
        ('group', allowed_resource, 'All', True)
    ]:
        upsert_permission(
            ZOOKEEPER,
            realm,
            resource_id,
            resource_type=resource_type,
            operation=operation,
            extended_acl=wildcard
        )
    '''
    login(CC_API_USER, CC_API_PASSWORD)
    list_environments()
    acl_list()
    logout()
    pass


if __name__ == '__main__':
    COMMANDS = {
        'ADD_SUPERUSER': create_superuser,
        'GRANT_SUPERUSER': grant_superuser,
        'ADD_TENANT': create_tenant,
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    try:
        fn = COMMANDS[command]
        args = sys.argv[2:]
        fn(*args)
    except Exception as e:
        LOGGER.error(str(e))
        sys.exit(1)

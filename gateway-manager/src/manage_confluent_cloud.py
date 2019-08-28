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


from dataclasses import dataclass
import re

import pexpect

from helpers import get_logger
from settings import (
    CC_CLI_PATH,
    CC_API_USER,
    CC_API_PASSWORD
)


LOGGER = get_logger('ConfluentCloud')


SA_REG = re.compile(
    r'''\s*(?P<id>.+?(?=\s*\\|))(?:\s*\|\s)(?P<name>.+?(?=\s*\\|))(?:\s*\|\s)(?P<desc>.+?(?=\s*\\r))'''
)


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
    for line in lines:
        match = SA_REG.match(line)
        if not match:
            continue
        _id = int(match.group('id'))
        name = match.group('name')
        desc = match.group('desc')
        accounts.append(ServiceAccount(_id, name, desc))
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
#   Utilities
#
#####################################

def _inline(s: str):
    # removes whitespace and newlines and replaces with single space for logs
    return ' '.join(s.split())

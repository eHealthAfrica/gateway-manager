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
from time import sleep

from helpers import get_logger
from zookeeper_functions import (
    make_user,
    upsert_permission,
    get_zookeeper,
    get_tenant_password
)

ZK_LAG_TIME = 3
LOGGER = get_logger('Kafka')


def create_superuser(name, password):
    # make user for name
    LOGGER.info(f'Creating SuperUser: {name}')
    make_user(ZOOKEEPER, name, password)
    sleep(ZK_LAG_TIME)
    grant_superuser(name)


def grant_superuser(name):
    # give user permission on all name artifacts in kafka
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


def create_tenant(realm):
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


def tenant_creds(realm):
    pw = get_tenant_password(realm)
    LOGGER.info(f'{realm} : {pw}')


if __name__ == '__main__':
    COMMANDS = {
        'ADD_SUPERUSER': create_superuser,
        'GRANT_SUPERUSER': grant_superuser,
        'ADD_TENANT': create_tenant,
        'KAFKA_CREDS': tenant_creds
    }

    command = sys.argv[1]
    if command.upper() not in COMMANDS.keys():
        LOGGER.critical(f'No command: {command}')
        sys.exit(1)

    try:
        ZOOKEEPER = get_zookeeper()

        fn = COMMANDS[command]
        args = sys.argv[2:]
        fn(*args)
    except Exception as e:
        LOGGER.error(str(e))
        sys.exit(1)

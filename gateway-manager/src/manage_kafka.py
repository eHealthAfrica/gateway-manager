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

from zookeeper_functions import (
    make_user,
    upsert_permission,
    zookeeper,
    get_tenant_password
)

ZK_LAG_TIME = 3


def create_superuser(name, password):
    # make user for name
    print(f'\nCreating Kafka SuperUser: {name}')
    make_user(zookeeper, name, password)
    sleep(ZK_LAG_TIME)
    # give user permission on all name artifacts in kafka
    for resource_type, resource_id in [
        ('topic', '*'),
        ('group', '*'),
        ('cluster', 'kafka-cluster'),
    ]:
        upsert_permission(
            zookeeper,
            name,
            resource_id,
            resource_type=resource_type,
            operation='All',
            extended_acl=False
        )


def create_tenant(realm):
    # make user for realm
    print(f'\nCreating Kafka Tenant for realm: {realm}')
    pw = get_tenant_password(realm)
    make_user(zookeeper, realm, pw)
    sleep(ZK_LAG_TIME)
    # give user permission on all realm artifacts in kafka
    allowed_resource = f'{realm}-'
    for resource_type, resource_id, operation, wildcard in [
        ('topic', allowed_resource, 'All', True),
        ('group', allowed_resource, 'All', True)
    ]:
        upsert_permission(
            zookeeper,
            realm,
            resource_id,
            resource_type=resource_type,
            operation=operation,
            extended_acl=wildcard
        )


if __name__ == "__main__":
    commands = {
        'ADD_SUPERUSER': create_superuser,
        'ADD_TENANT': create_tenant
    }
    command = sys.argv[1]
    args = sys.argv[2:]
    if command.upper() not in commands.keys():
        raise KeyError(f'No command: {command}')
    fn = commands[command]
    fn(*args)

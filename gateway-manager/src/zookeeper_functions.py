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


import logging
import json
import sys

import kazoo
from kazoo.client import KazooClient

from cryptography import zk_config, pbkdf2_hmac_sha256
from settings import (
    ZK_HOST,
    ZK_USER,
    ZK_PW,
    KAFKA_ADMIN_SECRET
)

# kafka ZK paths
USER_CHANGES_PATH = '/config/changes'
USER_CHANGES_FORMAT = 'config_change_'

EXTENDED_ACL_PATH = '/kafka-acl-extended/prefixed'
EXTENDED_ACL_CHANGES_PATH = '/kafka-acl-extended-changes'

ACL_PATH = '/kafka-acl'
ACL_CHANGES_PATH = '/kafka-acl-changes'
ACL_CHANGES_FORMAT = 'acl_changes_'


# Use the shared (internally) KafkaSecret to get the password for a user
def get_tenant_password(tenant_name):
    seed = f'{tenant_name}{KAFKA_ADMIN_SECRET}'
    return pbkdf2_hmac_sha256(seed, 'kafka')


# Print contents of Zookeeper path
def loot(zk, path):
    data, stat = zk.get(path)
    if data:
        try:
            readable = json.dumps(json.loads(data), indent=2)
        except json.decoder.JSONDecodeError:
            readable = data
        acl = zk.get_acls(path)
        print(f'{path} has data:\n{acl}\n\t{readable}')
    for i in zk.get_children(path):
        new_path = f'{path}/{i}'
        try:
            loot(zk, new_path)
        except kazoo.exceptions.NoAuthError as noer:
            print(f'!! Could not access {new_path}\n{zk.get_acls(path)}\n{noer}')


# Get the ID of the next change
def get_next_change(zk, path=None, format=None):
    changes = zk.get_children(path)
    if not changes:
        next_change = str(0)
    else:
        # get a string representing the 1 + the last number included in existing changes
        next_change = str(
            1 + max(
                [int(i.split(format)[1]) for i in changes]
            )
        )
    # make a template of zeros of correct length
    template = '0' * 10
    # format it and return
    return format + template[:-(len(next_change))] + next_change


# Report that a user's config has changed
def report_user_change(zk, user):
    next_change = get_next_change(zk, USER_CHANGES_PATH, USER_CHANGES_FORMAT)
    path = f'{USER_CHANGES_PATH}/{next_change}'
    acl = zk.default_acl[:]
    # make change globally readable
    acl.append(
        kazoo.security.make_acl('world', 'anyone', read=True)
    )
    data = {
        'version': 2,
        'entity_path': f'users/{user}'
    }
    zk.create(path, json.dumps(data).encode('utf-8'), acl=acl)


# Report that an ACL has been updated
def report_acl_change(zk, resource_type, resource_id, extended_acl=False):
    acl_change_path = (EXTENDED_ACL_CHANGES_PATH
                       if extended_acl
                       else ACL_CHANGES_PATH)
    next_change = get_next_change(zk, acl_change_path, ACL_CHANGES_FORMAT)

    path = f'{acl_change_path}/{next_change}'
    acl = zk.default_acl[:]
    # make change globally readable
    acl.append(
        kazoo.security.make_acl('world', 'anyone', read=True)
    )
    if extended_acl:
        data = {
            'version': 1,
            'resourceType': resource_type,
            'name': resource_id,
            'patternType': 'PREFIXED'
        }
        zk.create(path, json.dumps(data).encode('utf-8'), acl=acl)
    else:
        data = f'{resource_type}:{resource_id}'
        zk.create(path, data.encode('utf-8'), acl=acl)


# Remove a permission from a Kafka User
def remove_permission(
    zk,
    user,
    resource_id,
    resource_type='topic',
    type_='Allow',
    operation='Read',
    extended_acl=False
):
    acl_path = EXTENDED_ACL_PATH if extended_acl else ACL_PATH
    resource_type = resource_type.capitalize()
    acl_path = f'{acl_path}/{resource_type}/{resource_id}'
    principal = f'User:{user}'
    print(acl_path, principal)
    try:
        data, _ = zk.get(acl_path)
        data = json.loads(data)
    except kazoo.exceptions.NoNodeError:
        data = {
            'version': 1,
            'acls': []
        }
    else:
        filtered_acls = list(filter(
            lambda acl: acl['principal'] != principal or acl['operation'] != operation,
            data['acls']
        ))
        data['acls'] = filtered_acls
    if not data.get('acls', []):
        zk.delete(acl_path)
    else:
        zk.set(acl_path, json.dumps(data).encode('utf-8'))
    report_acl_change(zk, resource_type, resource_id, extended_acl=extended_acl)


# Grant a Kafka Permission to a User
def upsert_permission(
    zk,
    user,
    resource_id,
    resource_type='topic',
    operation='Read',
    type_='Allow',
    extended_acl=False
):
    resource_type = resource_type.capitalize()
    acl_path = EXTENDED_ACL_PATH if extended_acl else ACL_PATH
    acl_path = f'{acl_path}/{resource_type}/{resource_id}'
    principal = f'User:{user}'
    print(acl_path, principal)
    try:
        data, _ = zk.get(acl_path)
        data = json.loads(data)
    except kazoo.exceptions.NoNodeError:
        data = {
            'version': 1,
            'acls': []
        }
    else:
        acls = list(filter((
            lambda acl: acl['principal'] != principal or acl['operation'] != operation),
            data['acls']
        ))
        data['acls'] = acls

    new_acl = {
        'principal': principal,
        'permissionType': type_,
        'operation': operation,
        'host': '*'
    }
    data['acls'].append(new_acl)

    acl = zk.default_acl[:]
    # make change globally readable
    acl.append(
        kazoo.security.make_acl('world', 'anyone', read=True)
    )
    try:
        zk.create(acl_path, json.dumps(data).encode('utf-8'), acl=acl)
    except kazoo.exceptions.NodeExistsError:
        zk.set(acl_path, json.dumps(data).encode('utf-8'))
    report_acl_change(zk, resource_type, resource_id, extended_acl=extended_acl)


# Create a Kafka user
def make_user(zk, name, pw):
    creds = zk_config(password=pw)
    # create cred with default, admin ACL
    try:
        zk.create(f'/config/users/{name}', json.dumps(creds).encode('utf-8'))
    except kazoo.exceptions.NodeExistsError:
        zk.set(f'/config/users/{name}', json.dumps(creds).encode('utf-8'))
    # report change so brokers pick them up
    report_user_change(zk, name)


logging.basicConfig()

# constructor components
default_acl = kazoo.security.make_acl('sasl', ZK_USER, all=True)
sasl_options = {
    'mechanism': 'DIGEST-MD5',
    'username': ZK_USER,
    'password': ZK_PW
}

# Requires unreleased feature from Kazoo 2.7.x to get the digest to work properly
# In released version, sasl_options isn't part of the constructor and doesn't work

zookeeper = KazooClient(
    hosts=ZK_HOST,
    sasl_options=sasl_options,
    default_acl=[default_acl]
)
zookeeper.start()

if __name__ == '__main__':
    # when run directly, you can view entities within zookeeper for debugging
    starting_path = sys.argv[1] or ''
    loot(zookeeper, starting_path)

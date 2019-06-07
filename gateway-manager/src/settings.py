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

import os


def get_env(name, default=None):
    return os.environ.get(name, default)


DEBUG = bool(get_env('DEBUG'))

BASE_HOST = get_env('BASE_HOST')  # External URL for host
DOMAIN = get_env('BASE_DOMAIN')
PLATFORM_NAME = get_env('PLATFORM_NAME')
REALM_TEMPLATE_PATH = get_env(
    'REALM_TEMPLATE_PATH',
    '/code/realm/realm_template.json'
)

LOGIN_THEME = get_env('LOGIN_THEME')


# Keycloak Information
KEYCLOAK_INTERNAL = get_env('KEYCLOAK_INTERNAL')

KC_URL = f'{KEYCLOAK_INTERNAL}/keycloak/auth/'  # internal
KC_ADMIN_USER = get_env('KEYCLOAK_GLOBAL_ADMIN')
KC_ADMIN_PASSWORD = get_env('KEYCLOAK_GLOBAL_PASSWORD')
KC_MASTER_REALM = 'master'
KEYCLOAK_AETHER_CLIENT = get_env('KEYCLOAK_AETHER_CLIENT', 'aether')
KEYCLOAK_KONG_CLIENT = get_env('KEYCLOAK_KONG_CLIENT', 'kong')


# Kong Information
PUBLIC_REALM = get_env('PUBLIC_REALM', '-')
KONG_URL = get_env('KONG_INTERNAL')
KONG_OIDC_PLUGIN = 'kong-oidc-auth'

REALMS_PATH = '/code/realm'
SERVICES_PATH = '/code/service'
SOLUTIONS_PATH = '/code/solution'


# Kafka && Zookeeper

ZK_HOST = get_env('ZOOKEEPER_HOST')  # '127.0.0.1:32181'
# registered administrative credentials
KAFKA_ADMIN_SECRET = get_env('KAFKA_SECRET')
ZK_USER = get_env('ZOOKEEPER_USER')  # 'zk-admin'
ZK_PW = get_env('ZOOKEEPER_PW')  # 'password'

# Minio
MINIO_INTERNAL = get_env('MINIO_INTERNAL')

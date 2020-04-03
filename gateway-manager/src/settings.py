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

# External URL for host (includes protocol)
BASE_HOST = get_env('BASE_HOST')
BASE_DOMAIN = get_env('BASE_DOMAIN')
BASE_USE_SSL = BASE_HOST.startswith('https://')

APPS_PATH = get_env('APPS_PATH', '/code/app')
SERVICES_PATH = get_env('SERVICES_PATH', '/code/service')
SOLUTIONS_PATH = get_env('SOLUTIONS_PATH', '/code/solution')

_TEMPLATES_PATH = get_env('TEMPLATES_PATH', '/code/templates')
TEMPLATES = {
    'cors': get_env(
        'CORS_TEMPLATE_PATH',
        f'{_TEMPLATES_PATH}/cors_template.json'
    ),
    'oidc': get_env(
        'OIDC_TEMPLATE_PATH',
        f'{_TEMPLATES_PATH}/oidc_template.json'
    ),

    'realm': get_env(
        'REALM_TEMPLATE_PATH',
        f'{_TEMPLATES_PATH}/realm_template.json'
    ),

    'client': get_env(
        'CLIENT_TEMPLATE_PATH',
        f'{_TEMPLATES_PATH}/client_template.json'
    ),

    'user': {
        'admin': get_env(
            'ADMIN_TEMPLATE_PATH',
            f'{_TEMPLATES_PATH}/user_admin_template.json'
        ),

        'standard': get_env(
            'USER_TEMPLATE_PATH',
            f'{_TEMPLATES_PATH}/user_standard_template.json'
        ),
    },

    'es': {
        'role': get_env(
            'ES_ROLE_TEMPLATE_PATH',
            f'{_TEMPLATES_PATH}/es_role_template.json'
        ),
    },
    'es7': {
        'role': get_env(
            'ES_ROLE_TEMPLATE_PATH',
            f'{_TEMPLATES_PATH}/es7_role_template.json'
        ),
    }
}


# Keycloak Information

KC_ADMIN_URL = get_env('KEYCLOAK_INTERNAL')     # http://keycloak:8080/auth/
KC_ADMIN_USER = get_env('KEYCLOAK_GLOBAL_ADMIN')
KC_ADMIN_PASSWORD = get_env('KEYCLOAK_GLOBAL_PASSWORD')
KC_ADMIN_REALM = get_env('KEYCLOAK_MASTER_REALM', 'master')


# Kong Information

KONG_INTERNAL_URL = get_env('KONG_INTERNAL')    # http://kong:8001
KONG_PUBLIC_REALM = get_env('PUBLIC_REALM', '-')


# Kafka && Zookeeper

ZK_HOST = get_env('ZOOKEEPER_HOST')             # 127.0.0.1:32181
ZK_USER = get_env('ZOOKEEPER_USER')             # zk-admin
ZK_PW = get_env('ZOOKEEPER_PW')                 # password
# registered administrative credentials
KAFKA_ADMIN_SECRET = get_env('KAFKA_SECRET')

# Confluent Cloud

CC_CLI_PATH = get_env('CC_CLI_PATH', 'ccloud')
CC_API_USER = get_env('CC_API_USER')
CC_API_PASSWORD = get_env('CC_API_PASSWORD')
CC_ENVIRONMENT_NAME = get_env('CC_ENVIRONMENT_NAME', 'default')
CC_CLUSTER_NAME = get_env('CC_CLUSTER_NAME', 'default')


# ElasticSearch / Kibana

ES_HOST = get_env('ELASTICSEARCH_HOST')
ES_USER = get_env('ELASTICSEARCH_USER')
ES_PW = get_env('ELASTICSEARCH_PW')

# Google OAuth 2.0 Client
GOOGLE_CLIENT_ID = get_env('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = get_env('GOOGLE_CLIENT_SECRET')

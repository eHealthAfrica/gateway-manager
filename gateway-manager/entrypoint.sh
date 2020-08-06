#!/usr/bin/env bash
#
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
#
set -Eeuo pipefail

VERSION_FILE="/var/tmp/VERSION"
if [ -f "$VERSION_FILE" ]; then
    VERSION=`cat $VERSION_FILE`
fi

function show_help {
    echo """
    Commands
    ----------------------------------------------------------------------------

    help:
        Shows this message.

    bash:
        Runs bash.

    eval:
        Evaluates shell command.


    Home App
    ----------------------------------------------------------------------------
    start_app:
        Starts the gateway tenant home app


    Keycloak
    ----------------------------------------------------------------------------

    keycloak_ready:
        Checks the keycloak connection. Returns status 0 on success.


    add_realm:
        Adds a new realm using a default realm template.

        Usage:  add_realm {realm} {*description}
                          {*login theme}
                          {*account theme}
                          {*admin theme}
                          {*email theme}


    add_admin:
        Adds or updates an admin user to an existing realm.

        Usage:  add_admin {realm} {username}
                          {*password} {*reset_password_on_first_login}


    add_user:
        Adds or updates a user to an existing realm.

        Usage:  add_user {realm} {username}
                         {*password} {*reset_password_on_first_login}


    add_user_group:
        Adds an existing user to an existing group on an existing realm.

        Usage:  add_user_group {realm} {username} {group_id}


    add_confidential_client | add_oidc_client:
        Adds a confidential client to an existing realm.
        Required for any realm that will use OIDC for authentication.

        Usage:  add_confidential_client {realm} {client-name}
                add_oidc_client {realm} {client-name}


    add_public_client:
        Adds a public client to an existing realm.
        Allows token generation.

        Usage:  add_public_client {realm} {client-name}


    decode_token:
        Decodes a Keycloak JSON Web Token (JWT).

        Usage:  decode_token {token}


    Kong
    ----------------------------------------------------------------------------

    kong_ready:
        Checks the Kong connection. Returns status 0 on success.


    register_app | add_app:
        Registers an app in Kong.

        Usage:  register_app {app-name} {app-internal-url}
                add_app {app-name} {app-internal-url}


    remove_app:
        Removes an app in Kong.

        Usage:  remove_app {app-name}


    add_service:
        Adds a service to an existing realm in Kong,
        using the service definition in ${SERVICES_PATH:-/code/service} directory.

        Usage:  add_service {service} {realm} {oidc-client}


    remove_service:
        Removes a service from an existing realm in Kong,
        using the service definition in ${SERVICES_PATH:-/code/service} directory.

        Usage:  remove_service {service} {realm}

        Remove in all realms:  remove_service {service}


    add_solution:
        Adds a package of services to an existing realm in Kong,
        using the solution definition in ${SOLUTION_PATH:-/code/solution} directory.

        Usage:  add_solution {solution} {realm} {oidc-client}


    remove_solution:
        Removes a package of services from an existing realm in Kong,
        using the solution definition in ${SOLUTION_PATH:-/code/solution} directory.

        Usage:  remove_solution {solution} {realm}

        Remove in all realms:  remove_solution {solution}


    Kafka
    ----------------------------------------------------------------------------

    add_kafka_su:
        Adds a Superuser to the Kafka Cluster.

        Usage:  add_kafka_su {username} {password}


    grant_kafka_su:
        Gives an existing user superuser status.

        Usage:  grant_kafka_su {username}


    add_kafka_tenant:
        Adds a kafka user for a tenant, and adds ACL to their namespace.

        Usage:  add_kafka_tenant {tenant}


    get_kafka_creds:
        Gets SASL Credential for a given kafka tenant.

        Usage:  get_kafka_creds {tenant}


    Confluent Cloud
    ----------------------------------------------------------------------------

    add_ccloud_su:
        Adds a Superuser to the CC Cluster.

        Usage:  add_ccloud_su {username}


    grant_ccloud_su:
        Gives an existing user superuser status.

        Usage:  grant_ccloud_su {username}


    delete_ccloud_su:
        Removes a Superuser and their credentials, account and permissions.

        Usage:  delete_ccloud_su {username}


    add_ccloud_tenant:
        Adds a ccloud user for a tenant, and adds ACL to their namespace.

        Usage:  add_ccloud_tenant {tenant}


    delete_ccloud_tenant:
        Removes a tenant and their credentials, account and permissions (Does not remove data / topics).

        Usage:  delete_ccloud_tenant {username}


    add_ccloud_key
        Adds a ccloud APIKey for a tenant.

        Usage:  add_ccloud_key {tenant} '{*description}'


    list_ccloud_tenants
        Lists previously registered tenants in CCloud cluster.

        Usage:  list_ccloud_tenants


    list_ccloud_acls
        Lists ACLs of CCloud tenants, or of a single tenant referenced by name

        Usage:  list_ccloud_acls {*tenant}


    list_ccloud_api_keys
        Lists active APIKeys on the cluster. (Names only)

        Usage:  list_ccloud_api_keys


    ElasticSearch
    ----------------------------------------------------------------------------

    elasticsearch_ready:
        Checks the ElasticSearch connection. Returns status 0 on success.


    setup_elasticsearch:
        Prepares ElasticSearch.

        Usage:  setup_elasticsearch


    add_elasticsearch_tenant:
        Adds a tenant to ElasticSearch.

        Usage:  add_elasticsearch_tenant {tenant}


    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Current version:  [${VERSION:-latest}]
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """
}

case "$1" in

    # --------------------------------------------------------------------------
    # Keycloak
    # --------------------------------------------------------------------------

    keycloak_ready )
        python /code/src/manage_keycloak.py READY
    ;;

    add_realm )
        python /code/src/manage_keycloak.py ADD_REALM "${@:2}"
    ;;

    add_admin )
        python /code/src/manage_keycloak.py ADD_ADMIN "${@:2}"
    ;;

    add_user )
        python /code/src/manage_keycloak.py ADD_USER "${@:2}"
    ;;

    add_user_group )
        python /code/src/manage_keycloak.py ADD_USER_GROUP "${@:2}"
    ;;

    add_confidential_client | add_oidc_client )
        python /code/src/manage_keycloak.py ADD_CONFIDENTIAL_CLIENT "${@:2}"
    ;;

    add_public_client )
        python /code/src/manage_keycloak.py ADD_PUBLIC_CLIENT "${@:2}"
    ;;

    decode_token )
        python /code/src/decode_token.py "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # Kong
    # --------------------------------------------------------------------------

    kong_ready )
        python /code/src/manage_kong.py READY
    ;;

    register_app | add_app )
        python /code/src/manage_kong.py APP ADD "${@:2}"
    ;;

    remove_app )
        python /code/src/manage_kong.py APP REMOVE "${@:2}"
    ;;

    add_service )
        python /code/src/manage_kong.py SERVICE ADD "${@:2}"
    ;;

    remove_service )
        python /code/src/manage_kong.py SERVICE REMOVE "${@:2}"
    ;;

    add_solution )
        python /code/src/manage_kong.py SOLUTION ADD "${@:2}"
    ;;

    remove_solution )
        python /code/src/manage_kong.py SOLUTION REMOVE "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # Kafka
    # --------------------------------------------------------------------------

    add_kafka_su )
        python /code/src/manage_kafka.py ADD_SUPERUSER "${@:2}"
    ;;

    grant_kafka_su )
        python /code/src/manage_kafka.py GRANT_SUPERUSER "${@:2}"
    ;;

    add_kafka_tenant )
        python /code/src/manage_kafka.py ADD_TENANT "${@:2}"
    ;;

    get_kafka_creds )
        python /code/src/manage_kafka.py KAFKA_CREDS "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # CCloud
    # --------------------------------------------------------------------------

    add_ccloud_su )
        python /code/src/manage_confluent_cloud.py ADD_SUPERUSER "${@:2}"
    ;;

    grant_ccloud_su )
        python /code/src/manage_confluent_cloud.py GRANT_SUPERUSER "${@:2}"
    ;;

    delete_ccloud_su )
        python /code/src/manage_confluent_cloud.py REMOVE_SUPERUSER "${@:2}"
    ;;

    add_ccloud_tenant )
        python /code/src/manage_confluent_cloud.py ADD_TENANT "${@:2}"
    ;;

    delete_ccloud_tenant )
        python /code/src/manage_confluent_cloud.py REMOVE_TENANT "${@:2}"
    ;;

    add_ccloud_key )
        python /code/src/manage_confluent_cloud.py CREATE_KEY "${@:2}"
    ;;

    list_ccloud_tenants )
        python /code/src/manage_confluent_cloud.py LIST_SERVICE_ACCOUNTS "${@:2}"
    ;;

    list_ccloud_acls )
        python /code/src/manage_confluent_cloud.py LIST_ACLS "${@:2}"
    ;;


    list_ccloud_api_keys )
        python /code/src/manage_confluent_cloud.py LIST_API_KEYS "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # ElasticSearch
    # --------------------------------------------------------------------------

    elasticsearch_ready )
        python /code/src/manage_elasticsearch.py READY
    ;;

    setup_elasticsearch )
        python /code/src/manage_elasticsearch.py SETUP
    ;;

    add_elasticsearch_tenant )
        python /code/src/manage_elasticsearch.py ADD_TENANT "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # Gateway Home
    # --------------------------------------------------------------------------

    start_app )
        python /code/src/manage_home_app.py START_APP
    ;;

    # --------------------------------------------------------------------------
    # Generic
    # --------------------------------------------------------------------------

    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac

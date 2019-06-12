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

function show_help {
    echo """
    Commands
    ----------------------------------------------------------------------------

    help:
        Shows this message.

    bash:
        Runs bash.

    eval:
        Evals shell command.


    Keycloak & Kong
    ----------------------------------------------------------------------------

    setup_auth:
        Registers Keycloak (the auth service) in Kong.

        Shortcut of: register_app auth {keycloak-internal-url}


    register_app:
        Registers App in Kong.

        Usage: register_app {app-name} {app-internal-url}


    add_realm:
        Adds a new realm using a default realm template.

        Usage: add_realm {realm} {description (optional)} {login theme (optional)}


    add_user:
        Adds a user to an existing realm.

        Usage: add_user {realm} {username}
                        {*password} {*is_administrator}
                        {*email} {*reset_password_on_login}


    add_confidential_client | add_oidc_client:
        Adds a confidential client to a realm.
        Required for any realm that will use OIDC for authentication.

        Usage: add_confidential_client {realm} {client-name}
               add_oidc_client {realm} {client-name}


    add_public_client:
        Adds a public client client to a realm.
        Allows token generation.

        Usage: add_public_client {realm} {client-name}


    add_service:
        Adds a service to an existing realm in Kong,
        using the service definition in /service directory.

        Usage: add_service {service} {realm} {oidc-client}


    remove_service:
        Removes a service from an existing realm in Kong,
        using the service definition in /service directory.

        Usage: remove_service {service} {realm}


    add_solution:
        Adds a package of services to an existing realm in Kong,
        using the solution definition in /solution directory.

        Usage: add_solution {solution} {realm} {oidc-client}


    remove_solution:
        Removes a package of services from an existing realm in Kong,
        using the solution definition in /solution directory.

        Usage: remove_solution {solution} {realm}


    keycloak_ready:
        Checks the keycloak connection. Returns status 0 on success.


    decode_token:
        Decodes a Keycloak JSON Web Token (JWT).

        Usage: decode_token {token}


    Kafka
    ----------------------------------------------------------------------------

    add_kafka_su:
        Adds a Superuser to the Kafka Cluster.

        Usage: add_kafka_su {username} {password}


    add_kafka_tenant:
        Adds a kafka user for a tenant, and adds ACL to their namespace.

        Usage: add_kafka_tenant {tenant}


    get_kafka_creds:
        Gets SASL Credential for a given kafka tenant.

        Usage: get_kafka_creds {tenant}

    """
}

case "$1" in

    # --------------------------------------------------------------------------
    # Keycloak & Kong
    # --------------------------------------------------------------------------

    setup_auth )
        python /code/src/register_app.py auth $KEYCLOAK_INTERNAL
    ;;

    register_app )
        python /code/src/register_app.py "${@:2}"
    ;;

    add_realm )
        python /code/src/manage_realm.py ADD_REALM "${@:2}"
    ;;

    add_user )
        python /code/src/manage_realm.py ADD_USER "${@:2}"
    ;;

    add_confidential_client | add_oidc_client )
        python /code/src/manage_realm.py ADD_CONFIDENTIAL_CLIENT "${@:2}"
    ;;

    add_public_client )
        python /code/src/manage_realm.py ADD_PUBLIC_CLIENT "${@:2}"
    ;;

    add_service )
        python /code/src/manage_service.py ADD SERVICE "${@:2}"
    ;;

    remove_service )
        python /code/src/manage_service.py REMOVE SERVICE "${@:2}"
    ;;

    add_solution )
        python /code/src/manage_service.py ADD SOLUTION "${@:2}"
    ;;

    remove_solution )
        python /code/src/manage_service.py REMOVE SOLUTION "${@:2}"
    ;;

    keycloak_ready )
        python /code/src/manage_realm.py KEYCLOAK_READY
    ;;

    decode_token )
        python /code/src/decode_token.py "${@:2}"
    ;;


    # --------------------------------------------------------------------------
    # Kafka
    # --------------------------------------------------------------------------

    add_kafka_su )
        python /code/src/manage_kafka.py ADD_SUPERUSER "${@:2}"
    ;;

    add_kafka_tenant )
        python /code/src/manage_kafka.py ADD_TENANT "${@:2}"
    ;;

    get_kafka_creds )
        python /code/src/manage_kafka.py KAFKA_CREDS "${@:2}"
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

#!/usr/bin/env bash
#
# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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
    bash             : run bash
    

    eval             : eval shell command

    
    setup_auth       : register Keycloak & Minio in Kong.

    
    add_realm        : adds a new realm using the default realm template
                       found in the /realm directory

                       usage: add_realm {realm}

    
    add_user         : adds a user to an existing realm.

                       usage: add_user {realm} {username} 
                              {*password} {*is_administrator}
                              {*email} {*reset_password_on_login}

    
    add_oidc_client  : adds the default kong client to a realm. Required for
                       any realm that will use OIDC for authentication.

                       usage: add_oidc_client <realm>


    add_service      : adds a service to an existing realm in Kong,
                       using the service definition in /service directory.

                       usage: add_service {service} {realm}

    
    remove_service   : removes a service from an existing realm in Kong,
                       using the service definition in /service directory.

                       usage: remove_service {service} {realm}

    
    add_solution     : adds a package of services to an existing realm in Kong,
                       using the solution definition in /solution directory.

                       usage: add_solution {solution} {realm}

    
    remove_solution  : removes a package of services from an existing realm in Kong,
                       using the solution definition in /solution directory.

                       usage: remove_solution {solution} {realm}

    
    keycloak_ready   : checks the keycloak connection. Returns status 0 on success.

                       usage: keycloak_ready
    
    decode_token     : decodes a JSON Web Token (JWT)

                       usage: decode_token {token}
    """
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    setup_auth )
        python /code/src/setup_auth.py
    ;;

    add_realm )
        python /code/src/manage_realm.py ADD_REALM "${@:2}"
    ;;

    add_user )
        python /code/src/manage_realm.py ADD_USER "${@:2}"
    ;;

    add_oidc_client )
        python /code/src/manage_realm.py ADD_OIDC_CLIENT "${@:2}"
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

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac

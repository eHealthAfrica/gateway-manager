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

import jwt
import sys

from helpers import request, get_logger, print_json
from settings import BASE_HOST


def decode_token(token):
    return jwt.decode(token, verify=False)


def check_jwt(token):
    tokeninfo = decode_token(token)
    print_json(logger.info, tokeninfo)

    iss_url = tokeninfo['iss']
    if not iss_url.startswith(BASE_HOST):
        logger.critical(f'This token does not belong to our host {BASE_HOST}')
        sys.exit(1)

    # go to iss
    realminfo = request(method='get', url=iss_url)
    print_json(logger.info, realminfo)

    # if this call fails the token is not longer valid
    userinfo = request(
        method='get',
        url=realminfo['token-service'] + '/userinfo',
        headers={'Authorization': '{} {}'.format(tokeninfo['typ'], token)},
    )
    print_json(logger.info, userinfo)


def get_userinfo(token):
    tokeninfo = decode_token(token)

    username = tokeninfo['preferred_username']
    given_name = tokeninfo.get('given_name')
    family_name = tokeninfo.get('family_name')

    if family_name and given_name:
        return f'{given_name} {family_name}'
    elif family_name:
        return family_name
    elif given_name:
        return given_name
    else:
        return username


if __name__ == '__main__':
    logger = get_logger('Keycloak')

    token = sys.argv[1]
    check_jwt(token)

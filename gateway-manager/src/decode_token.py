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

import json
import jwt
import sys

from helpers import request
from settings import BASE_HOST


def check_jwt(token):
    tokeninfo = jwt.decode(token, verify=False)
    print_json(tokeninfo)

    iss_url = tokeninfo['iss']
    if not iss_url.startswith(BASE_HOST):
        raise RuntimeError(f'This token does not belong to our host {BASE_HOST}')

    # go to iss
    realminfo = request(method='get', url=iss_url)
    print_json(realminfo)

    # if this call fails the token is not longer valid
    userinfo = request(
        method='get',
        url=realminfo['token-service'] + '/userinfo',
        headers={'Authorization': '{} {}'.format(tokeninfo['typ'], token)},
    )
    print_json(userinfo)


def print_json(data):
    print(json.dumps(data, indent=2))
    print('---------------------------------------')


if __name__ == '__main__':
    token = sys.argv[1]

    check_jwt(token)

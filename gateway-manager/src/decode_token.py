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


def decode_jwt(encoded):
    # the jwt we get from the middleware isn't encrypted or signed
    return jwt.decode(encoded, verify=False)


def print_json(data):
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    token = sys.argv[1]

    userinfo = decode_jwt(token)
    print_json(userinfo)

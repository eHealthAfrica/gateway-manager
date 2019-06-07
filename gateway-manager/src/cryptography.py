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

import base64
import binascii
import hashlib
import hmac
import random
import string
from passlib.hash import scram

'''  # noqa
Artifacts created like this in Kafka Container

    /usr/bin/kafka-configs --zookeeper zookeeper:32181 --alter --add-config 'SCRAM-SHA-256=[password=password],SCRAM-SHA-512=[password=password]' --entity-type users --entity-name admin
    Completed Updating config for entity: user-principal 'admin'.

yield this in zoo-keeper:
{
    'SCRAM-SHA-512': {
        'salt': 'cXc3anM3YXJiZ3VoaHRkemIxaHFuM3U2ZA==',
        'stored_key': '85WEgeZegMpDTNHKWI2UbGXyOH2OZlrdlq+Zd5cu8eQpUzEO9im34Q7NVGSKwwgrorDe13j44W46XtaMiswAhQ==',
        'server_key': 'V+PkLOfCwZf+kEqQEYgwVboGZFl1CbXuiBcsK/pEfspgieOoa/Y1koGSbBOb4YyZcCvtpNcm7iYupupUfPB5MQ==',
        'iterations': 4096
    },
    'SCRAM-SHA-256': {
        'salt': 'a3NxbHpyY3d5ZGFsaDN5ZnpvdGt1bGlkNA==',
        'stored_key': 'kz0SZ6dBzusqNtViK3ULM9W56fgcmVAL/s1/ihe9VKY=',
        'server_key': 'JZ/K4Omu8UEfo4uXAvqg/f/7gdUItuYCXD2cmbcXwwg=',
        'iterations': 4096
    }
}
This lib allows you to generate the same artifacts in python for insertion into ZK
'''


def pbkdf2_hmac_sha256(pw, salt, iterations=4096):
    dk = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=pw.encode('utf-8'),
        salt=salt.encode('utf-8'),
        iterations=iterations
    )
    return binascii.hexlify(dk).decode('utf-8')


def make_salt(size=25):
    return ''.join([random.choice(string.printable) for i in range(size)])


def hi(password, salt, rounds=4096, algo='sha-256'):
    # naming convention is inherited from the Java implemenetation
    return scram.derive_digest(password, salt, rounds, algo)


def hash(_str, algo=hashlib.sha256):
    # naming convention is inherited from the Java implemenetation
    _str = base64.b64decode(_str)
    return base64.b64encode(algo(_str).digest())


def digest_hmac(key, _bytes, algo):
    hmac_obj = hmac.new(key, digestmod=algo)
    hmac_obj.update(_bytes)
    return hmac_obj.digest()


def get_key(salted_password, key='Server Key', algo=hashlib.sha256):
    msg = key.encode('utf-8')
    res = digest_hmac(salted_password, msg, algo)
    return base64.b64encode(res)


def generate_artifacts(password, salt=None, rounds=4096):
    res = {}
    if not salt:
        salt = make_salt()
    for algo in ['SCRAM-SHA-512', 'SCRAM-SHA-256']:
        algo_name = algo.lower()
        algo_mod = hashlib.sha256 if '256' in algo_name else hashlib.sha512
        raw_digest = hi(password, salt, rounds, algo_name)
        server_key = get_key(raw_digest, key='Server Key', algo=algo_mod)
        client_key = get_key(raw_digest, key='Client Key', algo=algo_mod)
        stored_key = hash(client_key, algo=algo_mod)

        res[algo] = {
            'salt': str(base64.b64encode(salt.encode('utf-8')), 'utf-8'),
            'stored_key': str(stored_key, 'utf-8'),
            'server_key': str(server_key, 'utf-8'),
            'iterations': rounds

        }
    return res


def zk_config(password, salt=None, rounds=4096):
    res = {
        'version': 1,
        'config': {}
    }
    confs = generate_artifacts(password, salt, rounds)
    for key, conf in confs.items():
        stringified = ','.join(['='.join([str(k), str(v)]) for k, v in conf.items()])
        res['config'][key] = stringified
    return res

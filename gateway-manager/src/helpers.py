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
from string import Template
from typing import List, Tuple

import coloredlogs
import requests
from requests.exceptions import HTTPError

from settings import DEBUG, KC_ADMIN_REALM, KONG_PUBLIC_REALM


def check_realm(realm):
    # certain realms are forbidden to handle like:
    # - `KC_ADMIN_REALM`: `master`
    # - `KONG_PUBLIC_REALM`: `-`
    if realm in (KC_ADMIN_REALM, KONG_PUBLIC_REALM):
        raise RuntimeError(f'Forbidden realm {realm}')


def do_nothing(*args, **kwargs):
    pass


def identity(obj):
    return obj


def request(*args, **kwargs):
    _logger = get_logger('request')

    ignore_404 = kwargs.pop('ignore_404', False)
    try:
        # don't verify SSL certificate internally
        res = requests.request(*args, **kwargs, verify=False)
        res.raise_for_status()
        if res.status_code != 204:
            data = res.json()
            print_json(_logger.verbose, data)
            return data
        return None
    except HTTPError as he:
        __handle_exception(_logger, he, res, ignore_404)
    except Exception as e:
        __handle_exception(_logger, e)


def fill_template(template_str, mapping):
    # take only the required values for formatting
    swaps = {
        k: v
        for k, v in mapping.items()
        if ('{%s}' % k) in template_str
    }
    return template_str.format(**swaps)


def load_json_file(json_file_path, mapping=None):
    _logger = get_logger('json')

    try:
        with open(json_file_path) as _f:
            content = _f.read().replace('\n', '')
            if mapping:
                content = Template(content).safe_substitute(mapping)
            data = json.loads(content)
        return data
    except Exception as e:
        __handle_exception(_logger, e)


def print_json(printer, data):
    printer(json.dumps(data, indent=2))


def __handle_exception(logger, exception, res=None, ignore_404=False):
    if res is not None:
        if res.status_code == 404 and ignore_404:
            raise exception

        logger.error(str(res))
        if res.status_code != 204:
            print_json(logger.verbose, res.json())

    logger.error(str(exception))
    raise exception


def get_logger(name):
    logger = logging.getLogger(name)

    logging.addLevelName(15, 'VERBOSE')
    logging.addLevelName(25, 'NOTICE')
    logging.addLevelName(35, 'SUCCESS')

    def _verbose(msg):
        logger.log(15, msg)

    def _success(msg):
        logger.log(35, msg)

    def _notice(msg):
        logger.log(25, msg)

    logger.verbose = _verbose
    logger.notice = _notice
    logger.success = _success

    coloredlogs.install(
        level='DEBUG' if DEBUG else 'INFO',
        fmt='[%(name)s]  %(message)s',
        logger=logger,
        level_styles={
            'critical': {'color': 'red', 'bright': True, 'bold': True},
            'debug': {'color': 245},
            'error': {'color': 'red'},
            'info': {},
            'notice': {'color': 'magenta'},
            'success': {'color': 'green', 'bright': True},
            'verbose': {'color': 'cyan'},
            'warning': {'color': 'yellow'},
        },
    )

    return logger


def is_kwarg(arg, collector):
    try:
        k, v = arg.split('=')
    except ValueError:
        return False
    collector[k] = v
    return True


def categorize_arguments(argv) -> Tuple[List, dict]:
    kwargs = {}
    args = [i for i in argv if not is_kwarg(i, kwargs)]
    return args, kwargs

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

KONG_VERSION=1.3
GWM_VERSION=latest

function build_image {
    APP=$1
    VERSION=$2
    TRAVIS_COMMIT=${TRAVIS_COMMIT:-test}
    TAG="${APP}:${VERSION}"
    TAG_COMMIT="${APP}:${TRAVIS_COMMIT}"
    LINE="~~~~~~~~~~~~~~~"

    echo -e ""
    echo -e "\e[2m${LINE}\e[0m Building image: \e[1;92m${TAG}\e[0m \e[2m${LINE}\e[0m"
    echo -e ""

    docker build \
        --pull \
        --no-cache \
        --force-rm \
        --tag $TAG \
        --build-arg VERSION=$VERSION \
        ./$APP
    docker tag $TAG $TAG_COMMIT

    echo -e ""
    echo -e "\e[2m${LINE}\e[0m Built image: \e[1;92m${TAG}\e[0m \e[2m${LINE}\e[0m"
    echo -e ""
}



build_image gateway-manager ${GWM_VERSION}
build_image kong ${KONG_VERSION}

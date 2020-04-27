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

source scripts/build.sh || \
    ( echo -e "\033[91mRun this script from root folder\033[0m" && \
      exit 1 )

function build_and_push {
    APP=$1
    VERSION=$2
    IMAGE_REPO=ehealthafrica
    TAG="${IMAGE_REPO}/${APP}:${VERSION}"
    TAG_COMMIT="${IMAGE_REPO}/${APP}:${VERSION}-${TRAVIS_COMMIT}"
    LINE="==============="

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
    echo -e "\e[2m${LINE}\e[0m Pushing image: \e[1;92m${TAG}\e[0m \e[2m${LINE}\e[0m"
    echo -e ""

    docker push $TAG
    docker push $TAG_COMMIT

    echo -e ""
    echo -e "\e[2m${LINE}\e[0m Pushed image: \e[1;92m${TAG}\e[0m \e[2m${LINE}\e[0m"
    echo -e ""
}

# If there is no tag then create image for branch develop
GATEWAY_VERSION=${TRAVIS_TAG:-latest}
build_image gateway-home ${GWM_VERSION} gateway-manager/home
docker run \
    --volume $PWD/gateway-manager/build:/code/app/build \
    --rm gateway-home build
build_and_push  gateway-manager  $GATEWAY_VERSION

KONG_RELEASES=( "1.3" "1.4" "1.5" "2.0" "latest" )
for kong_version in "${KONG_RELEASES[@]}"; do
    build_and_push  kong  $kong_version
done

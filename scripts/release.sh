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

function build_and_push {
    APP=$1
    VERSION=${2:-latest}
    IMAGE_REPO=ehealthafrica
    TAG="${IMAGE_REPO}/${APP}:${VERSION}"

    echo "Building image: ${TAG}"
    docker build \
        --pull \
        --no-cache \
        --force-rm \
        --tag $TAG \
        ./$APP

    echo "Pushing image: ${TAG}"
    docker push $TAG
}

build_and_push gateway-manager
build_and_push kong

# Use HELM chart tag
# https://github.com/helm/charts/tree/master/stable/kong
build_and_push kong 1.1

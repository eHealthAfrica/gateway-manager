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

source ./scripts/lib.sh || \
    ( echo -e "\033[91mRun this script from root folder\033[0m" && \
      exit 1 )

# If there is no tag then create image for branch develop
GW_VERSION=${TRAVIS_TAG:-latest}

# GW Manager
build_and_push  gateway-manager  ${GW_VERSION}

# # Custom Kong
KONG_VERSION="2.0"
build_and_push  kong  ${KONG_VERSION}

docker tag  ehealthafrica/kong:${KONG_VERSION} ehealthafrica/kong:2
docker push ehealthafrica/kong:2

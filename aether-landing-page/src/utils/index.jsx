/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { GATHER, KIBANA, AETHER, KERNEL, ODK, SERVICE_ABOUT } from './constants'

import gatherIcon from '../assets/gather.png'
import kibanaIcon from '../assets/kibana.png'
import aetherIcon from '../assets/aether.png'

/**
 * Capitalizes a given string.
 *
 * @param {string} str
 */
export const capitalize = (str) => `${str[0].toUpperCase()}${str[1] ? str.slice(1) : ''}`

/**
 * Return a list of services for a given tenant
 *
 * @param {string} tenant
 */
export const getServices = (tenant = '', origin = window.location.origin) => [
  { name: GATHER, about: SERVICE_ABOUT[GATHER], icon: gatherIcon, link: `${origin}/${tenant}/${GATHER}` },
  { name: KIBANA, about: SERVICE_ABOUT[KIBANA], icon: kibanaIcon, link: `${origin}/${tenant}/${KIBANA}/kibana-app` },
  { name: '' },
  { name: AETHER, about: SERVICE_ABOUT[AETHER], icon: aetherIcon, link: `${origin}/${tenant}/${AETHER}` },
  { name: KERNEL, about: SERVICE_ABOUT[KERNEL], link: `${origin}/${KERNEL}` },
  { name: ODK, about: SERVICE_ABOUT[ODK], link: `${origin}/${ODK}` }
]
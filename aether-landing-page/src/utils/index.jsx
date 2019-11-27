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

import { SAMPLE_ABOUT } from './constants'

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
export const getServices = (tenant = '') => [
  { name: 'gather', about: SAMPLE_ABOUT, icon: gatherIcon, link: `/${tenant}/gather` },
  { name: 'kibana', about: SAMPLE_ABOUT, icon: kibanaIcon, link: `/${tenant}/kibana/kibana-app` },
  { name: '' },
  { name: 'aether', about: SAMPLE_ABOUT, icon: aetherIcon, link: `/${tenant}/aether` },
  { name: 'kernel', about: SAMPLE_ABOUT, link: '/kernel' },
  { name: 'odk', about: SAMPLE_ABOUT, link: '/odk' }
]

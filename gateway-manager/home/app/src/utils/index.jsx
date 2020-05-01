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

import { GATHER, KIBANA, AETHER, KERNEL, ODK, AETHER_UI } from './constants'

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
export const getServices = (availableServices = [], tenant = '', origin = window.location.origin) => {
    const tenant_path = tenant ? `${tenant}/` : ''
    const services = [
        { name: GATHER, icon: gatherIcon, link: `${origin}/${tenant_path}${GATHER}` },
        { name: KIBANA, icon: kibanaIcon, link: `${origin}/${tenant_path}${KIBANA}/kibana-app` },
        { name: AETHER, icon: aetherIcon, link: `${origin}/${tenant_path}${AETHER_UI}` },
        { name: KERNEL, link: `${origin}/${tenant_path}${KERNEL}` },
        { name: ODK, link: `${origin}/${tenant_path}${ODK}` }
    ]
    const activeServices = []
    services.forEach(service => {
        if (availableServices.includes(service.name) ||
            (service.name === AETHER && availableServices.includes(AETHER_UI))
        ) {
            activeServices.push(service)
        }
    })
    return activeServices
}

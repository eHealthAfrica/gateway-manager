/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import React from 'react'
import { FormattedMessage } from 'react-intl'
import { capitalize } from '../utils'
import { GATHER, AETHER, KERNEL, ODK, KIBANA } from '../utils/constants'

const getStyle = (color) => ({ fontSize: 25, margin: 5, color: `${color}` })

const withSymbols = (service, color) => (
  <span>
    <i style={getStyle(color)}>&lt;</i>
    {service}
    <i style={getStyle(color)}>&gt;</i>
  </span>
)

const getBrand = (service) => {
  switch (service) {
    case GATHER:
      return <b>{service}</b>
    case AETHER:
      return <span><b>ae</b>ther</span>
    case KERNEL:
      return withSymbols(capitalize(KERNEL), '#50aef3')
    case ODK:
      return withSymbols(ODK.toUpperCase(), '#d25b69')
    case KIBANA:
      return capitalize(KIBANA)
    default:
      return service
  }
}

const ServiceCard = ({ name, about, icon, link }) => name ? (
  <>
    <a href={link}>
      <div className={`${name}-card title-large`}>
        {icon && <img className='service-icon' src={icon} alt='icon' />}
        {getBrand(name)}
      </div>
    </a>
    <p className='service-about small'>
      <FormattedMessage id={`service.card.about.${name}`} defaultMessage={about} />
    </p>
  </>
) : <div className='-card' />

export default ServiceCard

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

export const DEFAULT_LOCALE = 'en'

export const GATHER = 'gather'
export const KIBANA = 'kibana'
export const AETHER = 'aether'
export const KERNEL = 'kernel'
export const AETHER_UI = 'kernel-ui'
export const ODK = 'odk'

export const SERVICE_ABOUT = {
  [GATHER]: `
    With Gather you can create and manage surveys and surveyors,
    monitor the progress of data collection, and explore, mask and download your data as it comes in.
  `,
  [KIBANA]: `
    Send your data to Kibana and create various types of charts,
    tables and maps for visualizing, analyzing, and exploring the data.
  `,
  [AETHER]: `
    Aether enables you to extract, mask and publish data to other platforms
    by creating a pipeline to map your existing data structure to your desired output.
  `,
  [KERNEL]: 'The Aether Kernel provides common functionality, such as logging and authentication',
  [ODK]: `
    Aether Core modules provide generally useful components for data input and application communication.
    The ODK module can be used to, for example, for serving XForms to ODK Collect.
  `
}

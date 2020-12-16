# Data

## services.json

The expected format for services file is:

```javascript
{
  // kong service name (unique among rest of services) and indicated in its service file.
  "service-name": {
    // a CSS class name defined in `/static/css/landing-page.css`
    "key": "service-name",
    // The HTML content to be displayed as service name
    "name": "<b>Demo</b> Service",
    // The service icon (optional)
    "icon": "/${public_realm}/demo-service/assets/logo.png",
    // link to the service, usually the service-name
    "link": "demo-service/web-app",
    // Service description to be included bellow the name (optional)
    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
  },

  // Possible Kibana entry
  "kibana": {
    "key": "kibana",
    "name": "<b>K</b>ibana",
    "icon": "/${public_realm}/gateway/static/images/kibana-white.png",
    "link": "kibana/kibana-app",
    "description": "Send your data to Kibana and create various types of charts, tables and maps for visualizing, analyzing, and exploring the data."
  }
}
```

Sample of Landing Page

```text

                                                               <user name>

<Tenant name>


Services

  +----------------------------+      +---------------------------+
  |                            |      |                           |
  |   <icon>  <service-name>   |      |      <service-name>       |
  |                            |      |                           |
  +----------------------------+      +---------------------------+
      <service-description>               <service-description>


```

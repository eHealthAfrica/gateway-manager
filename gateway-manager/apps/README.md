# App

An app represents an application and defines a set of public URLs.
The main difference between an app and a service is that the app cannot be added to a realm.


The expected format for each app file is:

```javascript
{
  // kong service name (unique among rest of apps and services)
  "name": "app-service-name",

  // internal host (behind kong)
  "host": "http://my-app:8888",

  // list of endpoints served behind Kong
  "paths": [
    "/path/to/resource-1",
    "/path/to/resource-2",
    "/path/to/resource-3"
  ]
}
```

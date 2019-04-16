# Service

A service represents an application and defines a set of public and protected urls
and the route to access to them.

The expected format for each service file is:

```javascript
{
  // service name (unique among rest of services)
  "name": "service-name",

  // internal host (behind kong)
  "host": "http://my-service:8888",

  // list of urls protected by "kong-oidc-auth" plugin
  // all of these urls provide the X-Outh-Token header
  // or are redirected to keycloak to authenticate
  "oidc_endpoints": [
    {
      // endpoint name (unique among rest of OIDC endpoints in this service)
      "name": "protected",

      // internal url
      "url": "/protect-me-please",

      // [optional] external url (defaults to /any-realm-name/service-name/endpoint-url)
      // use case: if the endpoint does not depend on any realm
      "route_path": null,

      // [optional] (defaults to "false")
      // indicates if the route path will be used to build the url to execute the internal call
      // use case: if the endpoint does not depend on any realm
      "strip_path": "false"

      // in this case:
      //   external call:
      //     http://external-domain/testing-realm/service-name/protect-me-please/my-path
      //   internal call:
      //     http://my-service:8888/testing-realm/service-name/protect-me-please/my-path
    },
    // ...
  ],

  // list of urls that are not protected by "kong-oidc-auth" plugin
  // the urls can be open or protected by another authentication method
  // like BASIC authentication, token authentication...
  "public_endpoints": [
    {
      // endpoint name (unique among rest of public endpoints in this service)
      "name": "public",

      // internal url
      "url": "/i-am-public/",

      // [optional] external url (defaults to /any-realm-name/service-name/endpoint-url)
      // use case: if the endpoint does not depend on any realm
      "route_path": "/my-service/public/",

      // [optional] (defaults to "false")
      // indicates if the route path will be used to build the url to execute the internal call
      // use case: if the endpoint does not depend on any realm
      "strip_path": "true"

      // in this case:
      //   external call:
      //     http://external-domain/my-service/public/my-path
      //   internal call:
      //     http://my-service:8888/i-am-public/my-path
    },
    // ...
  ]
}
```

To add a service to an existing realm in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth add_service "service-name" "realm-name"
```

To remove a service from an existing realm in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth remove_service "service-name" "realm-name"
```

To remove a service from ALL existing realms in Kong

```bash
docker-compose -f docker-compose-generation.yml run auth remove_service "service-name" "*"
```

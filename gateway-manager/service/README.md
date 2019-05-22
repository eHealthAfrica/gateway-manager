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

      // [optional] external url, defaults to "/{realm}/{name}{url}" where
      // {realm} is the realm name,
      // {name} is the service name and
      // {url} is the endpoint url.
      // use case: if the endpoint does not depend on any realm
      "route_path": null,

      // [optional] template to create an external url. Overrides default route_path.
      // Creates a path dynamically based on the following variables using string substitution.
      // {realm} is the realm name,
      // {name} is the service name
      // {url} is the endpoint url
      "template_path": null, // "/{realm}/#{name}" -> /testing-realm/#protected

      // [optional] (defaults to "false")
      // indicates if the route path will be used to build the url to execute the internal call
      // use case: if the endpoint does not depend on any realm
      "strip_path": "false"

      // in this case:
      //   external call:
      //     http://external-domain/testing-realm/service-name/protect-me-please/my-path
      //   internal call:
      //     http://my-service:8888/testing-realm/service-name/protect-me-please/my-path
      "oidc_override": {
        // [optional & advanced!]
        // provide overrides to the standard oidc configuration passed to Kong-Oidc        
        // Do not use this unless you absolutely have to.
        "config.user_keys": ["preferred_username", "email"]
      }

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

      // [optional] external url, defaults to "/{realm}/{name}{url}" where
      // {realm} is the realm name,
      // {name} is the service name and
      // {url} is the endpoint url.
      // use case: if the endpoint does not depend on any realm
      "route_path": "/my-service/public/",

      // [optional] template to create an external url. Overrides default route_path.
      // Creates a path dynamically based on the following variables using string substitution.
      // {realm} is the realm name,
      // {name} is the service name
      // {url} is the endpoint url
      "template_path": null, // "/{realm}/#{name}" -> /testing-realm/#public

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
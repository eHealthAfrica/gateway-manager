# Gateway Manager

This application is used to configure Keycloak+Kong installations,
locally or as part of a cluster.

## Service

A service represents an application and defines a set of public and protected
URLs and the routes to access to them.

Continues in [Service README](/gateway-manager/service/README.md)

## Solution

A solution gathers a set of services.

Continues in [Solution README](/gateway-manager/solution/README.md)

## Commands

All the commands are defined in the [`entrypoint.sh`](/gateway-manager/entrypoint.sh) file.

```bash
entrypoint.sh {command-name} {rest-of-arguments}
```

### Generic

#### `help`
Shows the help message with all the possible commands.

#### `bash`
Runs bash inside the container.

#### `eval`
Evals shell command inside the container.

### Keycloak

#### `keycloak_ready`
Checks the Keycloak connection. Returns status `0` on success.

#### `add_realm`
Adds a new realm in Keycloak using a default realm template.

```bash
add_realm {realm} {description (optional)} {login theme (optional)}
```

#### `add_user`
Adds a user to an existing realm in Keycloak.

```bash
add_user {realm} {username} \
         {*password} {*is_administrator} \
         {*email} {*reset_password_on_login}
```

#### `add_confidential_client` or `add_oidc_client`
Adds a confidential client to an existing realm in Keycloak.
Required for any realm that will use OIDC for authentication.

```bash
add_confidential_client {realm} {client-name}
# or
add_oidc_client {realm} {client-name}
```

#### `add_public_client`
Adds a public client to an existing realm in Keycloak.
Allows token generation.

```bash
add_public_client {realm} {client-name}
```

#### `decode_token`
Decodes a Keycloak JSON Web Token (JWT).

```bash
decode_token {token}
```

### Kong

#### `add_app` or `register_app`
Registers an app as a service in Kong and serves it behind Kong (like NGINX).

```bash
add_app {app-name} {app-internal-url}
# or
register_app {app-name} {app-internal-url}
```

#### `remove_app`
Removes an app in Kong.

```bash
remove_app {app_name}
```

#### `setup_auth`
Registers Keycloak (the **auth** service) in Kong.

Alias of:

```bash
register_app auth $KEYCLOAK_INTERNAL
```

#### `add_service`
Adds a service to an existing realm in Kong,
using the service definition in `SERVICES_PATH` directory.

```bash
add_service {service} {realm} {oidc-client}
```

#### `remove_service`
Removes a service from an existing realm in Kong,
using the service definition in `SERVICES_PATH` directory.

```bash
remove_service {service} {realm}

# removes service from all realms
remove_service {service}
# or
remove_service {service} "*"
```

> Note: the service will not be enterily removed if it's still used by another realm.

#### `add_solution`
Adds a package of services to an existing realm in Kong,
using the solution definition in `SOLUTION_PATH` directory.

```bash
add_solution {solution} {realm} {oidc-client}
```

#### `remove_solution`
Removes a package of services from an existing realm in Kong,
using the solution definition in `SOLUTION_PATH` directory.

```bash
remove_solution {solution} {realm}

# removes solution from all realms
remove_solution {solution}
# or
remove_solution {solution} "*"
```

> Note: the solution will not be enterily removed if it's still used by another realm.

### Kafka

#### `add_kafka_su`
Adds a Superuser to the Kafka Cluster.

```bash
add_kafka_su {username} {password}
```

#### `add_kafka_tenant`
Adds a kafka user for a tenant, and adds ACL to their namespace.

```bash
add_kafka_tenant {tenant}
```

#### `get_kafka_creds`
Gets SASL Credential for a given kafka tenant.

```bash
get_kafka_creds {tenant}
```

## Environment variables

### Generic

- `DEBUG`: Enables debug mode. Is `false` if unset or set to empty string,
  anything else is considered `true`.

- `BASE_DOMAIN`: Installation hostname.

- `BASE_HOST`: Installation hostname with protocol.

- `SERVICES_PATH`: Path to service files directory. Defaults to `/code/service`.

- `SOLUTIONS_PATH`: Path to solution files directory. Defaults to `/code/solution`.

- `TEMPLATES_PATH`: Path to template files directory.
  Defaults to `/code/templates`.

- `CORS_TEMPLATE_PATH`: Path to Kong service CORS plugin template file.
  This template is used with the `register_app` command.
  Defaults to `{TEMPLATES_PATH}/cors_template.json`.

- `OIDC_TEMPLATE_PATH`: Path to Kong service OIDC plugin template file.
  This template is used with the `add_service` and `add_solution` commands.
  Defaults to `{TEMPLATES_PATH}/oidc_template.json`.

- `REALM_TEMPLATE_PATH`: Path to keycloak realm template file.
  This template is used with the `add_solution` and `add_service` commands.
  Defaults to `{TEMPLATES_PATH}/realm_template.json`.

- `CLIENT_TEMPLATE_PATH`: Path to keycloak client template file.
  This template is used with the `add_confidential_client`, `add_oidc_client`
  and `add_public_client` commands.
  Defaults to `{TEMPLATES_PATH}/client_template.json`.

- `ADMIN_TEMPLATE_PATH`: Path to Keycloak admin user template file.
  This template is used with the `add_user` command while creating admin users.
  Defaults to `{TEMPLATES_PATH}/user_admin_template.json`.

- `USER_TEMPLATE_PATH`: Path to Keycloak standard user template file.
  This template is used with the `add_user` command while creating non admin users.
  Defaults to `{TEMPLATES_PATH}/user_standard_template.json`.

- `ES_ROLE_TEMPLATE_PATH`: Path to ElasticSearch role template file.
  This template is used with the `add_elasticsearch_tenant` command.
  Defaults to `{TEMPLATES_PATH}/es_role_template.json`.

### Keycloak

- `KEYCLOAK_INTERNAL`: Keycloak internal URL. Usually `http://keycloak:8080/auth/`.
  **Note**: Ending `/` is required to connect to admin console.
- `KEYCLOAK_MASTER_REALM`: Keycloak master realm name. Defaults to `master`.
- `KEYCLOAK_GLOBAL_ADMIN`: Keycloak admin user name in the master realm.
- `KEYCLOAK_GLOBAL_PASSWORD`: Keycloak admin user password in the master realm.

### Kong

- `KONG_INTERNAL`: Kong internal URL. Usually `http://kong:8001`.
- `PUBLIC_REALM`: Kong public realm. Defaults to `-`.

### Kafka && Zookeeper

- `ZOOKEEPER_HOST`: Zookeeper host address. Usually `127.0.0.1:32181`.
- `ZOOKEEPER_USER`: Zookeeper user name.
- `ZOOKEEPER_PW`: Zookeeper user password.
- `KAFKA_SECRET`: Kafka registered administrative credentials.

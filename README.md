# Gateway Manager

This application is used to configure Keycloak+Kong installations,
locally or as part of a cluster.

## Aether Landing Page

An app that serves as a UI for accessing different running services.

Continues in [Aether Landing Page README](/aether-landing-page/README.md)

## App

An app represents an application and defines a set of public URLs.
The main difference between an app and a service is that the app cannot be added to a realm.

Continues in [App README](/gateway-manager/app/README.md)

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
Evaluates shell command inside the container.

### Keycloak

#### `keycloak_ready`
Checks the Keycloak connection. Returns status `0` on success.

#### `add_realm`
Adds a new realm in Keycloak using a default realm template.

```bash
add_realm {realm} {description (optional)} \
          {login theme (optional)} \
          {account theme (optional)} \
          {admin theme (optional)} \
          {email theme (optional)}
```

#### `add_admin`
Adds or updates an admin user to an existing realm in Keycloak.

```bash
add_user {realm} {username} {*password} {*reset_password_on_login}
```

#### `add_user`
Adds or updates a user to an existing realm in Keycloak.

```bash
add_user {realm} {username} {*password} {*reset_password_on_login}
```

#### `add_user_group`
Adds an existing user to a group on an existing realm in Keycloak.

```bash
add_user_group {realm} {username} {group_id}
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

#### `kong_ready`
Checks the Kong connection. Returns status `0` on success.

#### `add_app` or `register_app`
Registers an app as a service in Kong,
using the app definition in `APPS_PATH` directory.

```bash
add_app {app-name}
# or
register_app {app-name}
```

> Note: The expected app file is `{APPS_PATH}/{app-name}.json`.

#### `remove_app`
Removes an app in Kong,
using the app definition in `APPS_PATH` directory.

```bash
remove_app {app-name}
```
> Note: The expected app file is `{APPS_PATH}/{app-name}.json`.

#### `add_service`
Adds a service to an existing realm in Kong,
using the service definition in `SERVICES_PATH` directory.

```bash
add_service {service-name} {realm} {oidc-client}
```

> Note: The expected service file is `{SERVICES_PATH}/{service-name}.json`.

#### `remove_service`
Removes a service from an existing realm in Kong,
using the service definition in `SERVICES_PATH` directory.

```bash
remove_service {service-name} {realm}

# removes service from all realms
remove_service {service-name}
# or
remove_service {service-name} "*"
```

> Note: The expected service file is `{SERVICES_PATH}/{service-name}.json`.

> Note: the service will not be entirely removed if it's still used by another realm.

#### `add_solution`
Adds a package of services to an existing realm in Kong,
using the solution definition in `SOLUTION_PATH` directory.

```bash
add_solution {solution-name} {realm} {oidc-client}
```

> Note: The expected solution file is `{SOLUTION_PATH}/{solution-name}.json`.

#### `remove_solution`
Removes a package of services from an existing realm in Kong,
using the solution definition in `SOLUTION_PATH` directory.

```bash
remove_solution {solution-name} {realm}

# removes solution from all realms
remove_solution {solution-name}
# or
remove_solution {solution-name} "*"
```

> Note: The expected solution file is `{SOLUTION_PATH}/{solution-name}.json`.

> Note: the solution will not be entirely removed if it's still used by another realm.

### Kafka

#### `add_kafka_su`
Adds a Superuser to the Kafka Cluster.

```bash
add_kafka_su {username} {password}
```

#### `grant_kafka_su`
Gives an existing user superuser status.

```bash
grant_kafka_su {username}
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

### Confluent Cloud

 > Note: You need the following environment variables to be set to manipulate CCloud.
 >  - CC_API_USER : a permissioned Confluent Cloud User
 >  - CC_API_PASSWORD: that user's password
 >  - CC_ENVIRONMENT_NAME: the name of the environment you want to use (or default)
 >  - CC_CLUSTER_NAME: the name of the cluster to modify


#### `add_ccloud_su`
Adds a Superuser to the Confluent Cloud Kafka Cluster.

```bash
add_ccloud_su {username} {password}
```

#### `grant_ccloud_su`
Gives an existing user superuser status.

```bash
grant_ccloud_su {username}
```

#### `delete_ccloud_su`
Removes a Superuser and their credentials, account and permissions.

```bash
delete_ccloud_su {username}
```

#### `add_ccloud_tenant`
Adds a kafka user for a tenant, and adds ACL to their namespace.

```bash
add_ccloud_tenant {tenant}
```

#### `delete_ccloud_tenant`
Removes a tenant and their credentials, account and permissions (Does not remove data / topics).

```bash
delete_ccloud_tenant {username}
```

#### `add_ccloud_key`
Adds a ccloud APIKey for a tenant.

```bash
add_ccloud_key {tenant} "{description (optional)}"
```

#### `list_ccloud_tenants`
Lists previously registered tenants in CCloud cluster.

```bash
list_ccloud_tenants
```

#### `list_ccloud_acls`
Lists ACLs of CCloud tenants, or of a single tenant referenced by name

```bash
list_ccloud_acls {tenant (optional) }
```

#### `list_ccloud_api_keys`
Lists active APIKeys on the cluster. (Names only)

```bash
list_ccloud_api_keys
```

### ElasticSearch

#### `elasticsearch_ready`
Checks the ElasticSearch connection. Returns status `0` on success.

#### `setup_elasticsearch`
Prepares ElasticSearch.

```bash
setup_elasticsearch
```

#### `add_elasticsearch_tenant`
Adds a tenant to ElasticSearch.

```bash
add_elasticsearch_tenant {tenant}
```

## Environment variables

### Generic

- `DEBUG`: Enables debug mode. Is `false` if unset or set to empty string,
  anything else is considered `true`.

- `BASE_DOMAIN`: Installation hostname.

- `BASE_HOST`: Installation hostname with protocol.

- `APPS_PATH`: Path to app files directory. Defaults to `/code/app`.

- `SERVICES_PATH`: Path to service files directory. Defaults to `/code/service`.

- `SOLUTIONS_PATH`: Path to solution files directory. Defaults to `/code/solution`.

### Templates

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

All of these templates are going to be parsed using the
[python template strings feature](https://docs.python.org/3/library/string.html#template-strings).
This means that even the keys or the values can contain `$-based` strings that
will be replaced with the environment variable or command argument values.

Some of the expected `$-based` strings are:
- `domain`: replaced with `BASE_DOMAIN` environment variable value.
- `host`: replaced with `BASE_HOST` environment variable value.
- `realm`: replaced with the `realm`command argument value.
- `tenant`: replaced with the `tenant` command argument value.
- `publicRealm`: replaced with `PUBLIC_REALM` environment variable value.
- `oidc_client_id`: replaced with the `oidc-client` command argument value.
- `oidc_client_secret`: replaced with `oidc` client secret fetched form Keycloak.
- `username`: replaced with the `username` command argument value.
- `email`: replaced with the `email` command argument value.

Review the code to get the expected strings in each case.

### Keycloak

- `KEYCLOAK_INTERNAL`: Keycloak internal URL. Usually `http://keycloak:8080/auth/`.
  **Note**: Ending `/` is required to connect to admin console.
- `KEYCLOAK_MASTER_REALM`: Keycloak master realm name. Defaults to `master`.
- `KEYCLOAK_GLOBAL_ADMIN`: Keycloak admin user name in the master realm.
- `KEYCLOAK_GLOBAL_PASSWORD`: Keycloak admin user password in the master realm.

### Kong

- `KONG_INTERNAL`: Kong internal URL. Usually `http://kong:8001`.
- `PUBLIC_REALM`: Kong public realm. Defaults to `-`.

### Kafka & Zookeeper

- `ZOOKEEPER_HOST`: Zookeeper host address. Usually `127.0.0.1:32181`.
- `ZOOKEEPER_USER`: Zookeeper user name.
- `ZOOKEEPER_PW`: Zookeeper user password.
- `KAFKA_SECRET`: Kafka registered administrative credentials.

### ElasticSearch

- `ELASTICSEARCH_HOST`: Elasticsearch internal URL. Usually `http://elasticsearch:9200`.
- `ELASTICSEARCH_USER`: Elasticsearch user name.
- `ELASTICSEARCH_PW`: Elasticsearch user password.

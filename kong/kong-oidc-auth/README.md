# Kong OIDC Auth
OpenID Connect authentication integration with the Kong Gateway

## Configuration
You can add the plugin with the following request:

```bash
$ curl -X POST http://kong:8001/apis/{api}/plugins \
    --data "name=kong-oidc-auth" \
    --data "config.app_login_redirect_url=https://yourapplication.com/loggedin/dashboard" \
    --data "config.authorize_url=https://oauth.something.net/openid-connect/authorize" \
    --data "config.client_id=SOME_CLIENT_ID" \
    --data "config.client_secret=SOME_SECRET_KEY" \
    --data "config.cookie_domain=.ehealthafrica.org" \
    --data "config.email_key=email" \
    --data "config.hosted_domain=ehealthafrica.org" \
    --data "config.pf_idp_adapter_id=CompanyIdOIDCStage" \
    --data "config.salt=b3253141ce67204b" \
    --data "config.scope=openid+profile+email" \
    --data "config.service_logout_url=https://iam.service/realm/logout" \
    --data "config.token_url=https://oauth.something.net/openid-connect/token" \
    --data "config.user_info_cache_enabled=false" \
    --data "config.user_keys=email,username" \
    --data "config.user_url=https://oauth.something.net/openid-connect/userinfo"
```

| Form Parameter | default | description |
| --- | --- | --- |
| `name` | | plugin name `kong-oidc-auth` |
| `config.allowed_roles` <br /> <small>Optional</small> | | An array of roles, any of which should grant access to this route. This will be checked against the `groups` field from your OIDC providers userinfo endpoint. You _must_ make roles available as `userinfo.groups` for this to work, otherwise enabling this option will block all users as their roles will not be retrievable. |
| `config.app_login_redirect_url` | | Needed for Single Page Applications to redirect after initial authentication successful, otherwise a proxy request following initial authentication would redirect data directly to a users browser! |
| `config.authorize_url` | | Authorization url of the OAUTH provider (the one to which you will be redirected when not authenticated) |
| `config.client_id` | | OAUTH Client Id |
| `config.client_secret` | | OAUTH Client Secret |
| `config.cookie_domain` | `ehealthafrica.org` | Specify the domain in which this cookie is valid for, realistically will need to match the gateway |
| `config.email_key` | | Key to be checked for hosted domain, taken from userinfo endpoint |
| `config.hosted_domain` | | Domain whose users must belong to in order to get logged in. Ignored if empty |
| `config.pf_idp_adapter_id` <br /> <small>Optional</small> | | OAUTH PingFederate Adaptor ID of the authorization request ex: `CompanyIdOIDCStage`, essentially points to the idp environment, ping federate specific only |
| `config.realm` <br /> <small>Optional</small> | | This value will be passed as `X-Oauth-realm` _if and only if_ it is included as part of the request URL. |
| `config.salt` | `b3253141ce67204b` | Salt for the user session token, must be 16 char alphanumeric |
| `config.scope` | | OAUTH scope of the authorization request |
| `config.service_logout_url` | | The URL for logouts in your IAM provider. Will be redirected to this URL when hitting urls ending in `/logout` |
| `config.token_url` | | The URL of the Oauth provider to request the access token |
| `config.user_info_cache_enabled` | | This enables storing the userInfo in Kong local cache which enables sending the entire requested user information to the backend service upon every request, otherwise user info only comes back occasionally and backend api service providers are required to validate the EOAuth Cookie Session with cached user information within their logic |
| `config.user_info_periodic_check` | `60` | Time in seconds between token checks |
| `config.user_keys` <br /> <small>Optional</small> | `username,email` | keys to extract from the `user_url` endpoint returned json, they will also be added to the headers of the upstream server as `X-OAUTH-XXX` |
| `config.user_url` | | The URL of the oauth provider used to retrieve user information and also check the validity of the access token |

Data available from the userinfo endpoint and included in the `config.user_keys` section will be included as headers following the pattern `X-Oauth-{field}` to upstream services.

**NOTES**:
Ping Federate requires you to authorize a callback URL, all proxies have a standard call back route of:
https://api-gateway.company.com/your/proxy/path/oauth2/callback

## Supported Kong Releases
Kong >= 1.0

## Source
https://github.com/Optum/kong-oidc-auth

local url = require "socket.url"

local function validate_url(value)
  local parsed_url = url.parse(value)
  if parsed_url.scheme and parsed_url.host then
    parsed_url.scheme = parsed_url.scheme:lower()
    if not (parsed_url.scheme == "http" or parsed_url.scheme == "https") then
      return false, "Supported protocols are HTTP and HTTPS"
    end
  end

  return true
end

return {
  fields = {
    allowed_roles            = {type = "array", default = {}},
    app_login_redirect_url   = {type = "string", default = "", required = false},
    authorize_url            = {type = "url", func = validate_url, required = true},
    client_id                = {type = "string", required = true},
    client_secret            = {type = "string", required = true},
    cookie_domain            = {type = "string", default = "ehealthafrica.org"},
    email_key                = {type = "string", default = ""},
    hosted_domain            = {type = "string", default = ""},
    pf_idp_adapter_id        = {type = "string", default = ""},
    realm                    = {type = "string", default = ""},
    salt                     = {type = "string", default = "b3253141ce67204b", required = true},
    scope                    = {type = "string", default = ""},
    service_logout_url       = {type = "string", default = "", required = false},
    token_url                = {type = "url", func = validate_url, required = true},
    use_ssl                  = {type = "boolean", default = false},
    user_info_cache_enabled  = {type = "boolean", default = false},
    user_info_periodic_check = {type = "number", default = 60, required = true},
    user_keys                = {type = "array", default = {"username", "email"}},
    user_url                 = {type = "url", func = validate_url, required = true}
  }
}

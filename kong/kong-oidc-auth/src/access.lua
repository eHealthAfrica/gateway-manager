local cjson = require "cjson.safe"
local singletons = require "kong.singletons"
local openssl_cipher = require "openssl.cipher"
local openssl_digest = require "openssl.digest"
local pl_stringx = require "pl.stringx"
local http = require "resty.http"

local _M = {}
local aes = openssl_cipher.new("AES-128-CBC")
local cookie_domain = nil
local salt = nil -- 16 char alphanumeric
local oauth2_callback = "/oauth2/callback"

--
-- HELPERS
--

-- Convenience function for logging objects... because LUA...
local function dump(o)
   if type(o) == "table" then
      local s = "{ "
      for k,v in pairs(o) do
         if type(k) ~= "number" then
            k = '"'..k..'"'
         end
         s = s.."["..k.."] = "..dump(v)..","
      end
      return s.."} "
   else
      return tostring(o)
  end
end


-- Checks if an object exists in a set
local function is_member(_obj, _set)
   for _,v in pairs(_set) do
      if v == _obj then
         return true
      end
   end
   return false
end


local function extract_cookies()
   if type(ngx.header["Set-Cookie"]) == "table" then
      return unpack(ngx.header["Set-Cookie"])
   end
   return ngx.header["Set-Cookie"]
end


function encode_token(token, conf)
   return ngx.encode_base64(
      aes:encrypt(openssl_digest.new("md5"):final(conf.client_secret), salt, true):final(token)
   )
end


function decode_token(token, conf)
   local status, token = pcall(
      function()
         return aes:decrypt(
            openssl_digest.new("md5"):final(conf.client_secret), salt, true):final(ngx.decode_base64(token)
         )
      end
   )

  if status then
      return token
   end
   return nil
end


function cookie_expires(value)
   if value == 0 then
      return "Path=/;Expires=Thu, Jan 01 1970 00:00:00 UTC;Max-Age=0;HttpOnly;"
   end
   return ";Path=/;Expires="..ngx.cookie_time(ngx.time() + value)..";Max-Age="..value..";HttpOnly;"
end

--
-- BASIC AUTH
--

-- Get A token via PasswordGrant
local function get_token_via_basic(user, pw, conf)
   local httpc = http:new()
   local res, err = httpc:request_uri(conf.token_url, {
      method = "POST",
      ssl_verify = false,
      body = "grant_type=password"..
         "&scope="..conf.scope..
         "&client_id="..conf.client_id..
         "&client_secret="..conf.client_secret..
         "&username="..user..
         "&password="..pw,
      headers = {
         ["Content-Type"] = "application/x-www-form-urlencoded",
      }
   })
   return res, err
end


-- Extract credential parts from {user}:{pw}
local function creds_from_basic(auth_str)
   local m, err = ngx.re.match(auth_str, "(?<user>[^:]+):(?<pw>[^:]+)", "ao")
   return m
end


-- Cache failure callback function that handles basicauth
local function token_from_basic(base64_basic, conf)
   local plain_text = ngx.decode_base64(base64_basic)
   local c = creds_from_basic(plain_text)

   if c["user"] == nil or c["pw"] == nil then
      return nil
   end

   local res, err = get_token_via_basic(c["user"], c["pw"], conf)
   if err then
      return nil
   end
   if res.status ~= 200 then
      return nil
   end

   local userJson = cjson.decode(res.body)
   return encode_token(userJson["access_token"], conf)
end


-- get Userinfo from AuthProvider's userinfo endpoint
local function get_user_info(access_token, callback_url, conf)
   local httpc = http:new()
   local res, err = httpc:request_uri(conf.user_url, {
      method = "GET",
      ssl_verify = false,
      headers = {
         ["Authorization"] = "Bearer "..access_token,
      }
   })

   -- redirect to auth if user result is invalid not 200
   if res.status ~= 200 then
      return redirect_to_auth(conf, callback_url)
   end

   local userJson = cjson.decode(res.body)
   return userJson
end


local function get_kong_key(eoauth_token, access_token, callback_url, conf)
   -- This will add a 28800 second (8 hour) expiring TTL on this cached value
   -- https://github.com/thibaultcha/lua-resty-mlcache/blob/master/README.md
   local user_info, err = singletons.cache:get(
      eoauth_token,
      { ttl = conf.user_info_periodic_check },
      get_user_info,
      access_token,
      callback_url,
      conf
   )

   if err then
      ngx.log(ngx.ERR, "Could not retrieve UserInfo: ", err)
      return
   end
   return user_info
end


local function validate_roles(conf, token)
   local _allowed_roles = conf.allowed_roles
   local _next = next(_allowed_roles)

   if _next == nil then
      return true -- no roles provided for checking. Ok.
   end

   if token["groups"] == nil then
      ngx.log(ngx.ERR, "oidc.userinfo.groups not availble! Check keycloak settings.")
      return false
   end

   for _, role in pairs(_allowed_roles) do
      if is_member(role, token["groups"]) then
         return true
      end
   end
   return false -- no matching roles
end


function redirect_to_auth(conf, callback_url)
   -- Track the endpoint they wanted access to so we can transparently redirect them back
   -- For Calls to indicate they prefer a 403 instead of redirect to the Oauth provider,
   -- a header of X-Oauth-Unauthorized can be set to `status_code | login`
   local login_pref = ngx.req.get_headers()["X-Oauth-Unauthorized"]
   if login_pref and login_pref == "status_code" then
      -- FIXME
      -- The status code should be HTTP_UNAUTHORIZED (401)
      -- For legacy reasons we need to keep HTTP_FORBIDDEN (403)
      return kong.response.exit(ngx.HTTP_FORBIDDEN, {
         message = "Forbidden: Auth redirect aborted on X-Oauth-Unauthorized == status_code"
      })
   end

   local redirect_back = ngx.var.request_uri
   if string.find(redirect_back, oauth2_callback) then
      redirect_back = conf.app_login_redirect_url
   end
   ngx.header["Set-Cookie"] = {
      "EOAuthRedirectBack="..redirect_back..cookie_expires(120),
      extract_cookies()
   }

   -- Redirect to the /oauth endpoint
   local oauth_authorize = conf.authorize_url.."?"..
      "&scope="..conf.scope..
      "&client_id="..conf.client_id..
      "&redirect_uri="..callback_url..
      "&response_type=code"

   if conf.pf_idp_adapter_id ~= "" then
      -- Ping Federate Auth URL
      oauth_authorize = oauth_authorize.."&pfidpadapterid="..conf.pf_idp_adapter_id
   end

   return ngx.redirect(oauth_authorize)
end


-- Logout Handling
function handle_logout(encrypted_token, conf)
   -- Terminate the Cookie
   local redirect_url = string.format(
      "%s?redirect_uri=%s",
      conf.service_logout_url,
      conf.app_login_redirect_url
   )

   ngx.header["Set-Cookie"] = {
      "EOAuthToken=;"..cookie_expires(0)..cookie_domain,
      extract_cookies()
   }
   if conf.realm then
      ngx.header["Set-Cookie"] = {
         "EOAuthRealm=;"..cookie_expires(0)..cookie_domain,
         extract_cookies()
      }
   end

   -- Remove session
   if conf.user_info_cache_enabled then
      singletons.cache:invalidate(encrypted_token)
   end
   -- Redirect to IAM service logout
   return ngx.redirect(redirect_url)
end


-- Callback Handling
function handle_callback(conf, callback_url)
   local args = ngx.req.get_uri_args()
   local code = args.code
   local redirect_url

   if args.redirect_url == nil then
      redirect_url = callback_url
   else
      redirect_url = args.redirect_url
   end

   if code then
      local httpc = http:new()
      local res, err = httpc:request_uri(conf.token_url, {
         method = "POST",
         ssl_verify = false,
         body = "grant_type=authorization_code"..
            "&code="..code..
            "&client_id="..conf.client_id..
            "&client_secret="..conf.client_secret..
            "&redirect_uri="..redirect_url,
         headers = {
            ["Content-Type"] = "application/x-www-form-urlencoded",
         }
      })

      if not res then
         return kong.response.exit(ngx.HTTP_INTERNAL_SERVER_ERROR, {
            message = "Failed to request: "..err
         })
      end

      local body_json = cjson.decode(res.body)
      local access_token = body_json.access_token
      if not access_token then
         -- ** DO NOT SHOW ERROR AND REDIRECT TO LOGIN PAGE **
         -- return kong.response.exit(ngx.HTTP_BAD_REQUEST, {
         --    message = body_json.error_description
         -- })
         return redirect_to_auth(conf, callback_url)
      end

      ngx.header["Set-Cookie"] = {
         "EOAuthToken="..encode_token(access_token, conf)..cookie_expires(1800)..cookie_domain,
         extract_cookies()
      }
      if conf.realm then
         ngx.header["Set-Cookie"] = {
            "EOAuthRealm="..conf.realm..cookie_expires(1800)..cookie_domain,
            extract_cookies()
         }
      end

      -- Support redirection back to Kong if necessary
      local redirect_back = ngx.var.cookie_EOAuthRedirectBack

      if redirect_back then
         -- Should always land here if no custom Logged in page defined!
         return ngx.redirect(redirect_back)
      else
         -- return redirect_to_auth(conf, callback_url)
         return
      end
   else
      return kong.response.exit(ngx.HTTP_UNAUTHORIZED, {
         message = "User has denied access to the resources"
      })
   end
end

--
-- MAIN Function that Kong runs
--

function _M.run(conf)
   local path_prefix = ""
   local callback_url = ""

   cookie_domain = "Domain="..conf.cookie_domain..";"
   salt = conf.salt

   -- Fix for /api/team/POC/oidc/v1/service/oauth2/callback?code=*******
   if ngx.var.request_uri:find("?") then
      path_prefix = ngx.var.request_uri:sub(1, ngx.var.request_uri:find("?") -1)
   else
      path_prefix = ngx.var.request_uri
   end

   local scheme = ""
   if conf.use_ssl then
      scheme = "https"
   else
      scheme = ngx.var.scheme
   end

   if pl_stringx.endswith(path_prefix, "/") then
      path_prefix = path_prefix:sub(1, path_prefix:len() - 1)
      callback_url = scheme.."://"..ngx.var.host..path_prefix..oauth2_callback
   elseif pl_stringx.endswith(path_prefix, oauth2_callback) then
      -- We are in the callback of our proxy
      callback_url = scheme.."://"..ngx.var.host..path_prefix
      handle_callback(conf, callback_url)
   else
      callback_url = scheme.."://"..ngx.var.host..path_prefix..oauth2_callback
   end

   -- See if we have a token

   -- Try to get token from Bearer string

   local auth_header = ngx.var.http_Authorization
   local access_token = nil
   local encrypted_token

   if auth_header then
      local _ -- Keep off the global scope
      _, _, access_token = string.find(auth_header, "Bearer%s+(.+)")
   end

   -- Try to Perform BasicAuth
   if auth_header and access_token == nil then
      local _ -- Keep off the global scope
      local base64_basic
      _, _, base64_basic = string.find(auth_header, "Basic%s+(.+)")

      if base64_basic then
         local err
         local hashed = encode_token(base64_basic, conf)

         encrypted_token, err = singletons.cache:get(
            "basicauth."..hashed,
            { ttl = conf.user_info_periodic_check },
            token_from_basic,
            base64_basic,
            conf
         )
         if not encrypted_token then
            return kong.response.exit(ngx.HTTP_UNAUTHORIZED, {
               message = "Invalid Credentials"
            })
         end
      end
   else
      -- Try to get token from cookie
      encrypted_token = ngx.var.cookie_EOAuthToken
   end

   -- No token, send to auth
   if encrypted_token == nil and access_token == nil then
      return redirect_to_auth(conf, callback_url)
   end

   if encrypted_token == nil then
      -- make an encoded token from the passed access_token
      encrypted_token = encode_token(access_token, conf)
   end
   -- check if we are authenticated already
   if access_token == nil then
      access_token = decode_token(encrypted_token, conf)
      if not access_token then
         -- broken access token
         return redirect_to_auth(conf, callback_url)
      end
   end

   -- They had a valid EOAuthToken so its safe to process a proper logout now.
   if pl_stringx.endswith(path_prefix, "/logout") then
      return handle_logout(encrypted_token, conf)
   end

   -- Make sure referer header is set for all HTTPS traffic
   if scheme == "https" and ngx.header["referer"] == nil then
      ngx.header["referer"] = scheme.."://"..ngx.var.host
   end

   -- Update the Cookie to increase longevity for 30 more minutes if active proxying
   ngx.header["Set-Cookie"] = {
      "EOAuthToken="..encode_token(access_token, conf)..cookie_expires(1800)..cookie_domain,
      extract_cookies()
   }
   if conf.realm then
      ngx.header["Set-Cookie"] = {
         "EOAuthRealm="..conf.realm..cookie_expires(1800)..cookie_domain,
         extract_cookies()
      }
   end

      -- CACHE LOGIC - Check boolean and then if EOAUTH has existing key -> user_info value
   if conf.user_info_cache_enabled then
      local user_info = get_kong_key(encrypted_token, access_token, callback_url, conf)
      if user_info then
         -- Check if allowed_roles is set && enforce
         local valid = validate_roles(conf, user_info)
         if valid == false then
            return kong.response.exit(ngx.HTTP_UNAUTHORIZED, {
               message = "User lacks valid role for this OIDC resource"
            })
         end

         for i, key in ipairs(conf.user_keys) do
            ngx.header["X-Oauth-".. key] = user_info[key]
            ngx.req.set_header("X-Oauth-".. key, user_info[key])
         end

         if conf.realm and pl_stringx.count(ngx.var.request_uri, conf.realm) > 0 then
            -- inject realm name into headers
            ngx.header["X-Oauth-realm"] = conf.realm
            ngx.req.set_header("X-Oauth-realm", conf.realm)
         end

         ngx.req.set_header("X-Oauth-Token", access_token)
         ngx.header["X-Oauth-Token"] = access_token
         return
      end
   end
   -- END OF NEW CACHE LOGIC --

   -- Get user info
   if not ngx.var.cookie_EOAuthUserInfo then
      local user_info = get_user_info(access_token, callback_url, conf)
      if user_info then
         -- Check if allowed_roles is set && enforce
         local valid = validate_roles(conf, user_info)
         if valid == false then
            return kong.response.exit(ngx.HTTP_UNAUTHORIZED, {
               message = "User lacks valid role for this OIDC resource"
            })
         end

         if conf.hosted_domain ~= "" and conf.email_key ~= "" then
            if not pl_stringx.endswith(user_info[conf.email_key], conf.hosted_domain) then
               return kong.response.exit(ngx.HTTP_UNAUTHORIZED, {
                  message = "Hosted domain is not matching"
               })
            end
         end

         for _, key in ipairs(conf.user_keys) do
            ngx.header["X-Oauth-".. key] = user_info[key]
            ngx.req.set_header("X-Oauth-".. key, user_info[key])
         end

         if conf.realm and pl_stringx.count(ngx.var.request_uri, conf.realm) > 0 then
            -- inject realm name into headers
            ngx.header["X-Oauth-realm"] = conf.realm
            ngx.req.set_header("X-Oauth-realm", conf.realm)
         end
         ngx.req.set_header("X-Oauth-Token", access_token)
         ngx.header["X-Oauth-Token"] = access_token

         ngx.header["Set-Cookie"] = {
            "EOAuthUserInfo=0;"..cookie_expires(conf.user_info_periodic_check),
            extract_cookies()
         }
      else
         return kong.response.exit(ngx.HTTP_INTERNAL_SERVER_ERROR, {
            message = "Could not get User info"
         })
      end
   end
end

return _M

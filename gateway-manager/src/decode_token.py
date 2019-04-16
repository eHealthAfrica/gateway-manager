
import json
import jwt
import sys


def decode_jwt(encoded):
    # the jwt we get from the middleware isn't encrypted or signed
    return jwt.decode(encoded, verify=False)


def print_json(data):
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    token = sys.argv[1]

    userinfo = decode_jwt(token)
    print_json(userinfo)

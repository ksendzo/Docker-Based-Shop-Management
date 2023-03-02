import json
from functools import wraps

from flask import Response, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roleCheck (role):
    def innerRole (function):
        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if (("roles" in claims) and (role in claims["roles"])):
                return function (*args, **kwargs)
            else:
                return Response(response=json.dumps({"msg": "Missing Authorization Header"}), status=401)
        return decorator
    return innerRole

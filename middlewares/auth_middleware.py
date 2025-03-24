from functools import wraps
from flask import request, jsonify
import jwt
import os
from dotenv import load_dotenv

import inspect

def ui_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = verify_token()
        if isinstance(user, dict):
            sig = inspect.signature(f)
            if "user" in sig.parameters:
                kwargs["user"] = user  # Pass only if `user` is expected
            return f(*args, **kwargs)
        return user
    return decorated_function


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

def verify_token():
    # print("verify_token")
    authorization = request.headers.get("Authorization")
    # handle the case where the token is empty
    # print(len(authorization.split(" ")))
    if len(authorization.split(" ")) < 2:
        return jsonify({"error": "Unauthorized"}), 401

    if not authorization:
        return jsonify({"error": "Unauthorized"}), 401
    token = authorization.split(" ")[1]
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

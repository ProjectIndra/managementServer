# from functools import wraps
# from flask import request, jsonify
# import jwt
# import os
# from dotenv import load_dotenv

# from models.authModels import users_collection

# import inspect

# def ui_login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         user = verify_token()
#         if isinstance(user, dict):
#             sig = inspect.signature(f)
#             if "user" in sig.parameters:
#                 kwargs["user"] = user  # Pass only if `user` is expected
#             return f(*args, **kwargs)
#         return user
#     return decorated_function


# load_dotenv()
# SECRET_KEY = os.getenv("SECRET_KEY")

# def verify_token():
#     # print("verify_token")
#     authorization = request.headers.get("Authorization")
#     # handle the case where the token is empty
#     # print(len(authorization.split(" ")))
#     if len(authorization.split(" ")) < 2:
#         return jsonify({"error": "Unauthorized"}), 401

#     if not authorization:
#         return jsonify({"error": "Unauthorized"}), 401
#     token = authorization.split(" ")[1]
#     if not token:
#         return jsonify({"error": "Unauthorized"}), 401
    
#     try:
#         decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         # check if the user is in the database
#         # if not, return a 404 error

#         print(decoded)
#         user = users_collection.find_one({"user_id": decoded.get("user_id")})
#         if not user:
#             return jsonify({"error": "Invalid User"}), 404

#         return decoded
#     except jwt.ExpiredSignatureError:
#         return jsonify({"error": "Token expired"}), 401
#     except jwt.InvalidTokenError:   
#         return jsonify({"error": "Invalid token"}), 401


from functools import wraps
from flask import request, jsonify, g  # Import `g` for global context
import jwt
import os
from dotenv import load_dotenv
from models.authModels import users_collection
import inspect

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

def ui_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = verify_token()
        if isinstance(user, dict):  # Token is valid, user is a dict
            sig = inspect.signature(f)
            if "user" in sig.parameters:
                kwargs["user"] = user  # Pass user details to function
            else:
                g.user = user  # Store in global context (`g`)
            return f(*args, **kwargs)
        return user  # If token is invalid, return the error response
    return decorated_function

def verify_token():
    authorization = request.headers.get("Authorization")
    if not authorization or len(authorization.split(" ")) < 2:
        return jsonify({"error": "Unauthorized"}), 401

    token = authorization.split(" ")[1]
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = users_collection.find_one({"user_id": decoded.get("user_id")})
        if not user:
            return jsonify({"error": "Invalid User"}), 404
        return decoded  # Return decoded token instead of JSON response
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

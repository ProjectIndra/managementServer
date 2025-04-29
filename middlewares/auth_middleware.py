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
from models.authModels import users_collection, cli_session_collection
import inspect
from datetime import datetime
from flask import g

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
    
    token=""


    if authorization.split(" ")[0] =="BearerCLI":      #means the request is from cli
        # print("cli authorization")
        token = authorization.split(" ")[1]
        # check the token in the db of cli session if its valid and not expired, here the token isn't a jwt token
        # it lies in the db of cli session
        try:
            # print(token)
            cli_details=cli_session_collection.find_one({"cli_session_token": token},{"cli_session_token_expiry_timestamp":1,"cli_id":1,"user_id":1})
            if not cli_details:
                return jsonify({"error": "Invalid token"}), 401
            # check if the token is expired or not
            expiry_str = cli_details.get("cli_session_token_expiry_timestamp")
            expiry_time = datetime.fromisoformat(expiry_str) if isinstance(expiry_str, str) else expiry_str
            
            if expiry_time < datetime.utcnow():
                return jsonify({"error": "Token expired"}), 401
            # check if the user is in the database
            # if not, return a 404 error
            user = users_collection.find_one({"user_id": cli_details.get("user_id")})
            if not user:
                return jsonify({"error": "Invalid User"}), 404
            # return the username and user_id
            return {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "cli_id": cli_details.get("cli_id")
            }
        except Exception as e:
            print(str(e))
            return jsonify({"error": str(e)}), 500
        
    elif authorization.split(" ")[0] == "Bearer":   #means the request is from ui
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
    
    else:
        return jsonify({"error": "Invalid token format"}), 401

import jwt
import uuid
from datetime import datetime, timedelta
from flask import request, jsonify, make_response
from flask_bcrypt import Bcrypt
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from marshmallow import ValidationError

# Internal imports
from models.authModels import user_schema, cli_session_schema
from models.authModels import users_collection, cli_session_collection


bcrypt = Bcrypt()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key").encode()  # Ensure it's bytes
cipher = Fernet(SECRET_KEY)


def get_user_details(user):
    try:
        # authorization = request.headers.get("Authorization")
        # token = authorization.split(" ")[1]
        # if not token:
        #     return jsonify({"error": "Token from cookie is required"}), 400

        # decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # user_id = decoded_token.get("user_id")

        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400

        user_response = users_collection.find_one({"user_id": user_id},{"_id":0,"password":0,"cli_verification_token":0,"cli_verification_token_expiry_timestamp":0})
        if not user_response:
            return jsonify({"error": "User not found"}), 404

        # user_response.pop("password")  # Remove password before sending response
        # user_response.pop("_id")  # Remove _id field
        # user_response.pop("cli_verification_token")  # Remove cli_verification_token field   

        return jsonify(user_response), 200
    
    # except jwt.ExpiredSignatureError:
    #     return jsonify({"error": "Token has expired"}), 401
    # except jwt.InvalidTokenError:
    #     return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def update_user_details(user):
    """
    This function is responsible for updating the user details.
    """
    try:
        data = request.json
        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Validate input data
        # validated_data = user_schema.load(data)  # Validate input
        profile_name=data.get("profile_name")
        profile_image=data.get("profile_image")
        

        # Update the user details in the database
        result = users_collection.update_one({"user_id": user_id}, {"$set": {"profile_name": profile_name, "profile_image": profile_image}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "No changes made or user not found"}), 404

        return jsonify({"message": "User details updated successfully"}), 200
    
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

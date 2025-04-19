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

def get_cli_verification_token(user):
    try:
        user_id=user.get("user_id")
        
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        cli_verification_token=str(uuid.uuid4())
        #update the cli_verification_token in the db
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"cli_verification_token": cli_verification_token, "cli_verification_token_expiry_timestamp": datetime.utcnow() + timedelta(days=1)}}
        )

        return jsonify({"cli_verification_token": cli_verification_token}), 200
    
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def verify_cli_token():
    try:
        data = request.json
        token = data.get("cli_verification_token")
        wireguard_endpoint = data.get("wireguard_endpoint")
        wireguard_public_key = data.get("wireguard_public_key")

        if not wireguard_endpoint or not wireguard_public_key:
            return jsonify({"error": "WireGuard IP and Public Key are required"}), 400


        if not token:
            return jsonify({"error": "Verification token is required"}), 400
        

        # update the cli status to inactive and first check if the old_cli_id is present in the db or not
        old_cli = cli_session_collection.find_one({"cli_verification_token": token})
        if old_cli:
            #deactivate the old cli
            old_cli_id = old_cli.get("cli_id")
            cli_session_collection.update_one(
                {"cli_id":old_cli_id,"cli_verification_token": token},
                {"$set": {"cli_status": False}}
            )   

        # check if the new cli verification token is present in the db or not
        user = users_collection.find_one({"cli_verification_token": token},{"_id": 0, "user_id": 1})
        if not user:
            return jsonify({"error": "Invalid token"}), 401
        user_id=user.get("user_id")

        cli_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())
        session_expiry_time = (datetime.utcnow() + timedelta(days=365)).isoformat()

        session_data = {
            "user_id": user_id,
            "cli_id": cli_id,
            "cli_wireguard_endpoint": wireguard_endpoint,
            "cli_wireguard_public_key": wireguard_public_key,
            "cli_status": True,
            "cli_session_token": session_token,
            "cli_session_token_expiry_timestamp": session_expiry_time,
            "cli_verification_token": token
        }
        cli_session_schema.load(session_data)  # Validate session data
        cli_session_collection.insert_one(session_data)

        return jsonify({
            "message": "Token verified successfully",
            "session_token": session_token
        }), 200
    
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
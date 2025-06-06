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
            {"$set": {"cli_verification_token": cli_verification_token}}
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
    
def get_all_cli_details(user):
    """
    This function returns all CLI session details for a user where cli_status is True.
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Fetch all active CLI session details for the user
        cli_sessions = list(cli_session_collection.find(
            {"user_id": user_id, "cli_status": True},
            {"_id": 0}
        ))

        if not cli_sessions:
            return jsonify({"error": "No active session found"}), 404

        return jsonify({"cli_session_details": cli_sessions}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

def delete_cli_session(user):
    """
    This function will delete the cli session for a user.
    This will update the cli_status to False in the db using the cli_id and user_id.
    """
    try:
        user_id = user.get("user_id")
        cli_id = request.args.get("cli_id")
        if not user_id or not cli_id:
            return jsonify({"error": "User ID and CLI ID are required"}), 400
        
        # Check if the CLI session exists
        cli_session = cli_session_collection.find_one({"user_id": user_id, "cli_id": cli_id})
        if not cli_session:
            return jsonify({"error": "CLI session not found"}), 404
        # Check if the CLI session is already inactive
        if not cli_session.get("cli_status"):
            return jsonify({"error": "CLI session is already inactive"}), 400

        # Update the cli_status to False in the db
        result = cli_session_collection.update_one(
            {"user_id": user_id, "cli_id": cli_id},
            {"$set": {"cli_status": False}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "No changes made or session not found"}), 404

        return jsonify({"message": "CLI session deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


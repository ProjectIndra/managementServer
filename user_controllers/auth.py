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
from models.authModels import user_schema, user_session_schema
from models.authModels import users_collection, sessions_collection

bcrypt = Bcrypt()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key").encode()  # Ensure it's bytes
cipher = Fernet(SECRET_KEY)


def register():
    try:
        data = request.json
        data["user_id"] = str(uuid.uuid4())  # Generate user_id before validation

        # validate email and password . email should contain @ and password should be atleast 6 characters long
        if "@" not in data["email"]:
            return jsonify({"error": "Invalid email"}), 400
        if len(data["password"]) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        if len(data["username"]) < 3:
            return jsonify({"error": "Username must be at least 3 characters long"}), 400
        
        validated_data = user_schema.load(data)  # Validate input

        if users_collection.find_one({"email": validated_data["email"]}):
            return jsonify({"error": "Email already exists"}), 400

        validated_data["password"] = bcrypt.generate_password_hash(validated_data["password"]).decode("utf-8")

        try:
            users_collection.insert_one(validated_data)
        except Exception as db_error:
            return jsonify({"error": "Database error: " + str(db_error)}), 500

        return jsonify({"message": "User registered successfully"}), 201

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def login():
    try:
        data = request.json
        username_or_email = data.get("username_or_email")
        password = data.get("password")

        if not username_or_email or not password:
            return jsonify({"error": "Username/email and password are required"}), 400

        # Find user by username or email
        user = users_collection.find_one({
            "$or": [{"email": username_or_email}, {"username": username_or_email}]
        })

        if not user or not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid username/email or password"}), 401

        # Generate JWT token
        payload = {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        
        return jsonify({"message": "Login successful", "token": token}), 200    

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_cli_verification_token():
    try:
        token = request.cookies.get("token")
        if not token:
            return jsonify({"error": "Token from cookie is required"}), 400

        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")

        user = users_collection.find_one({"user_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        encrypted_token = cipher.encrypt(user_id.encode()).decode()
        expiry_time = datetime.utcnow() + timedelta(days=30)

        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "cli_verification_token": encrypted_token,
                "cli_verification_token_expiry_timestamp": expiry_time
            }}
        )

        return jsonify({"cli_verification_token": encrypted_token}), 200
    
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

        if not token:
            return jsonify({"error": "Verification token is required"}), 400

        decrypted_user_id = cipher.decrypt(token.encode()).decode()

        user = users_collection.find_one({"user_id": decrypted_user_id})
        if not user:
            return jsonify({"error": "Invalid token"}), 401

        expiry_time = user.get("cli_verification_token_expiry_timestamp")
        if not expiry_time or datetime.utcnow() > expiry_time:
            return jsonify({"error": "Token expired"}), 401

        client_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())
        session_expiry_time = datetime.utcnow() + timedelta(days=30)

        session_data = {
            "user_id": decrypted_user_id,
            "client_id": client_id,
            "cli_session_token": session_token,
            "cli_session_token_expiry_timestamp": session_expiry_time
        }
        user_session_schema.load(session_data)  # Validate session data

        sessions_collection.insert_one(session_data)

        return jsonify({
            "message": "Token verified successfully",
            "user_id": decrypted_user_id,
            "client_id": client_id,
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

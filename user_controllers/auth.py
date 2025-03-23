import jwt
import uuid
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_bcrypt import Bcrypt
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Internal imports
from dbConnection import db
from models import authModels  # Import models and schema

bcrypt = Bcrypt()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")


def register():
    try:
        data = request.json

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if authModels.users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already exists"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_id = str(uuid.uuid4())  # Generate a unique user ID

        new_user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": hashed_password
        }
        
        authModels.users_collection.insert_one(new_user)

        return jsonify({"message": "User registered successfully"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def login():
    try:
        data = request.json
        
        username_or_email = data.get('username_or_email')
        password = data.get('password')

        if not username_or_email or not password:
            return jsonify({"error": "Username/email and password are required"}), 400

        user = authModels.users_collection.find_one({
            "$or": [{"email": username_or_email}, {"username": username_or_email}]
        })

        if user and bcrypt.check_password_hash(user['password'], password):
            # Load SECRET_KEY properly
            load_dotenv()
            SECRET_KEY = os.getenv("SECRET_KEY")

            if not SECRET_KEY:
                return jsonify({"error": "Server configuration error: SECRET_KEY is missing"}), 500

            payload = {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "exp": datetime.utcnow() + timedelta(hours=24)  # Token expiry
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return jsonify({"message": "Login successful", "token": token}), 200
        else:
            return jsonify({"error": "Invalid username/email or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_cli_verificationToken():
    """
    Generates a verification token using details from the JWT token in the Authorization header.
    """
    try:
        auth_header = request.headers.get("Authorization")
        print(auth_header)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        load_dotenv()
        SECRET_KEY = os.getenv("SECRET_KEY")

        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user_id = decoded_token.get("user_id")
        username = decoded_token.get("username")
        email = decoded_token.get("email")

        user = authModels.users_collection.find_one({"user_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404

        
        cipher = Fernet(SECRET_KEY)
        encrypted_token = cipher.encrypt(user_id.encode()).decode()

        # Set expiry time to 1 month from now
        expiry_time = datetime.utcnow() + timedelta(days=30)

        authModels.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "cli_verification_token": encrypted_token,
                "cli_verification_token_expiry_timestamp": expiry_time
            }}
        )

        return jsonify({"token": encrypted_token}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def verify_cli_token():
    """
    Verifies the CLI token, decrypts it, and creates a UUID-based session token.
    A new unique client_id is generated for each request and stored separately in the session collection.
    """
    try:
        data = request.json
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token is required"}), 400

        load_dotenv()
        SECRET_KEY = os.getenv("SECRET_KEY")
        cipher = Fernet(SECRET_KEY)

        try:
            decrypted_user_id = cipher.decrypt(token.encode()).decode()
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        user = authModels.users_collection.find_one({"user_id": decrypted_user_id})
        if not user:
            return jsonify({"error": "Invalid token"}), 401

        expiry_time = user.get("cli_verification_token_expiry_timestamp")
        if not expiry_time or datetime.utcnow() > expiry_time:
            return jsonify({"error": "Token expired"}), 401

        # Generate unique client_id and session token
        client_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())
        session_expiry_time = datetime.utcnow() + timedelta(days=30)

        # Store the session details in the session collection
        authModels.sessions_collection.insert_one({
            "user_id": decrypted_user_id,
            "client_id": client_id,
            "cli_session_token": session_token,
            "cli_session_token_expiry_timestamp": session_expiry_time
        })

        return jsonify({
            "message": "Token verified successfully",
            "user_id": decrypted_user_id,
            "client_id": client_id,
            "session_token": session_token
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

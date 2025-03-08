from flask import request, jsonify
from flask_bcrypt import Bcrypt

# internal import
from dbConnection import db
from models import authModels  # Import models and schema

bcrypt = Bcrypt()

# Register Route
def register():
    data = request.json
    
    # Validate input
    errors = authModels.user_schema.validate(data)
    if errors:
        return jsonify({"error": errors}), 400

    username = data['username']
    email = data['email']
    password = data['password']

    if authModels.users_collection.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password
    }
    authModels.users_collection.insert_one(new_user)

    return jsonify({"message": "User registered successfully"}), 201

# Login Route
def login():
    data = request.json
    username_or_email = data.get('username_or_email')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    user = authModels.users_collection.find_one({
        "$or": [{"email": username_or_email}, {"username": username_or_email}]
    })

    if user and bcrypt.check_password_hash(user['password'], password):
        return jsonify({"message": "Login successful", "user": user["username"]}), 200
    else:
        return jsonify({"error": "Invalid username/email or password"}), 401

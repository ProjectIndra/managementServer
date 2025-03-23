from dbConnection import db  # Use the existing database connection
from marshmallow import Schema, fields

# Schema for user details and verification token
class UserSchema(Schema):
    user_id = fields.String(required=True)
    username = fields.String(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=lambda x: len(x) >= 6)
    cli_verification_token = fields.String()
    cli_verification_token_expiry_timestamp = fields.DateTime()

# Schema for CLI session token (supports multiple clients per user)
class UserSessionSchema(Schema):
    user_id = fields.String(required=True)  # Link session to user
    client_id = fields.String(required=True)  # Identify different clients
    cli_session_token = fields.String()
    cli_session_token_expiry_timestamp = fields.DateTime()

# Initialize schemas
user_schema = UserSchema()
user_session_schema = UserSessionSchema()

# Define collections
users_collection = db["users"]  # Stores user details + verification token
sessions_collection = db["user_sessions"]  # Stores session tokens per client

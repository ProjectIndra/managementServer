from dbConnection import db  # Use the existing database connection
from marshmallow import Schema, fields

# Schema for user details and verification token
class userSchema(Schema):
    user_id = fields.String(required=True)
    username = fields.String(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=lambda x: len(x) >= 6)
    cli_verification_token = fields.String()
    profile_name=fields.String()
    profile_image=fields.String()

# Schema for CLI session token (supports multiple clis per user)
class cliSessionSchema(Schema):
    user_id = fields.String(required=True)  # Link session to user
    cli_id = fields.String(required=True)  # Identify different clis
    cli_session_token = fields.String()
    cli_session_token_expiry_timestamp = fields.DateTime()
    cli_wireguard_endpoint = fields.String(required=True)
    cli_wireguard_public_key = fields.String(required=True)
    cli_status = fields.Boolean(default=True)  # Active by default

# Initialize schemas
user_schema = userSchema()
cli_session_schema = cliSessionSchema()

# Define collections
users_collection = db["users"]  # Stores user details + verification token
cli_session_collection = db["cli_sessions"]  # Stores session tokens per cli

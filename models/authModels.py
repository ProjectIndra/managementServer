from dbConnection import db  # Use the existing database connection
from marshmallow import Schema, fields

class UserSchema(Schema):
    username = fields.String(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=lambda x: len(x) >= 6)

user_schema = UserSchema()

# Define users collection
users_collection = db["users"]

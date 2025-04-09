from dbConnection import db  # Use the existing database connection
from marshmallow import Schema, fields

# Schema for hdfs details
class hdfsSchema(Schema):
    user_id = fields.String(required=True)
    name = fields.String(required=True) # name of the file or folder
    path = fields.String(required=True) # path of the file or folder
    type = fields.String(required=True)
    description = fields.String()
    permission = fields.String()
    size = fields.String()
    createdAt = fields.DateTime()
    lastModified = fields.String()
    is_deleted = fields.Boolean(default=False) # default is false


# Initialize schema
hdfs_schema = hdfsSchema()
# Define collections
hdfs_collection = db["hdfs_details"]  # Stores hdfs details
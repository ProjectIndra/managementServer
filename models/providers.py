from dbConnection import db  # Import your DB connection
from marshmallow import Schema, fields

class providerSchema(Schema):
    user_id= fields.String(required=True) #this is the user id of the provider user or we can say provider_user_id
    provider_id = fields.String(required=True)
    provider_name = fields.String(required=True)
    # provider_type = fields.String(required=True,default="ubuntu") #not needed here , only for vm it's needed
    provider_status = fields.String(required=True)
    provider_ram_capacity = fields.String(required=True)
    provider_vcpu_capacity = fields.String(required=True)
    provider_storage_capacity = fields.String(required=True)
    provider_used_ram = fields.String()
    provider_used_vcpu = fields.String()
    provider_used_storage = fields.String()
    provider_used_vms = fields.String()
    provider_used_networks = fields.String()
    provider_rating = fields.Float(required=True)
    provider_url= fields.String(required=True)
    management_server_verification_token = fields.String()
    # provider_deleted = fields.Boolean(default=False)
    # provider_deleted_at = fields.DateTime()

class confSchema(Schema):
    provider_id = fields.String(required=True)
    provider_allowed_ram = fields.String(required=True)
    provider_allowed_vcpu = fields.String(required=True)
    provider_allowed_storage = fields.String(required=True)
    provider_allowed_vms = fields.String(required=True)
    provider_allowed_networks = fields.String(required=True)
    conf_created_at = fields.DateTime(required=True)
    conf_updated_at = fields.DateTime(required=True)

provider_schema = providerSchema()
conf_schema = confSchema()

provider_details_collection = db["providers_details"]  # MongoDB collection for providers
provider_conf_collection = db["providers_conf"]  # MongoDB collection for provider conf
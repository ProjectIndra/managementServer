from dbConnection import db  # Import your DB connection
from marshmallow import Schema, fields

class VMStatusSchema(Schema):
    vm_id = fields.String(required=True)
    vm_name = fields.String()
    status = fields.String(required=True)
    provider_id = fields.String() #id of the provider server not the provider user
    client_user_id = fields.String(required=True)
    vm_deleted = fields.Boolean(default=False)
    vm_deleted_at = fields.DateTime()

# defining the schema for wireguard connection details
class WireguardConnectionDetailsSchema(Schema):
    wireguard_ip = fields.String()
    wireguard_public_key = fields.String()
    wireguard_status = fields.String()
    cli_id = fields.String()

class VMDetailsSchema(Schema):
    provider_user_id = fields.String(required=True)
    client_user_id = fields.String(required=True)
    vm_id = fields.String(required=True)
    vm_name = fields.String() #only reference for user
    provider_id = fields.String()
    provider_name = fields.String(required=True)
    vcpu = fields.String(required=True)
    ram = fields.String(required=True)
    storage = fields.String(required=True)
    vm_image_type = fields.String(required=True)
    #  wireguard_connection_details which is array of json objects , stores wireguard_ip,wireguard_public_key,wireguard_ip and cli_id
    wireguard_connection_details = fields.List(fields.Nested(lambda: WireguardConnectionDetailsSchema()))
    internal_vm_name = fields.String() #internal reference
    vm_created_at = fields.DateTime(required=True)



vm_status_schema = VMStatusSchema()
vm_details_schema = VMDetailsSchema()

vm_status_collection = db["vm_status"]  # MongoDB collection for VMs
vm_details_collection = db["vm_details"]  # MongoDB collection for VM details

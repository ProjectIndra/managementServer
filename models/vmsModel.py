from dbConnection import db  # Import your DB connection
from marshmallow import Schema, fields

class VMStatusSchema(Schema):
    vm_id = fields.String(required=True)
    vm_name = fields.String()
    status = fields.String(required=True)
    provider_id = fields.String()
    vm_deleted = fields.Boolean(default=False)
    vm_deleted_at = fields.DateTime()


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
    wireguard_ip =fields.String()
    wireguard_public_key = fields.String()
    wireguard_endpoint = fields.String()
    wireguard_status=fields.Boolean()
    internal_vm_name = fields.String() #internal reference
    vm_created_at = fields.DateTime(required=True)

vm_status_schema = VMStatusSchema()
vm_details_schema = VMDetailsSchema()

vm_status_collection = db["vm_status"]  # MongoDB collection for VMs
vm_details_collection = db["vm_details"]  # MongoDB collection for VM details

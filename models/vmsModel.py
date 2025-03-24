from dbConnection import db  # Import your DB connection
from marshmallow import Schema, fields

class VMStatusSchema(Schema):
    user_id = fields.String(required=True)
    vm_id = fields.String(required=True)
    vm_name = fields.String()
    status = fields.String(required=True)

class VMDetailsSchema(Schema):
    user_id = fields.String(required=True)
    vm_id = fields.String(required=True)
    vm_name = fields.String()
    provider_id = fields.String()
    provider_name = fields.String(required=True)
    vcpu = fields.String(required=True)
    ram = fields.String(required=True)
    storage = fields.String(required=True)
    wireguard_ip =fields.String()
    wireguard_public_key = fields.String()
    wireguard_endpoint = fields.String()
    internal_vm_name = fields.String()

vm_status_schema = VMStatusSchema()
vm_details_schema = VMDetailsSchema()

vm_status_collection = db["vm_status"]  # MongoDB collection for VMs
vm_details_collection = db["vm_details"]  # MongoDB collection for VM details

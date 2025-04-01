from flask import jsonify, request
import requests

# internal imports
from models.providers import provider_details_collection, provider_conf_collection
from models.providers import provider_schema, conf_schema
from dbConnection import db
from datetime import datetime

def update_provider_conf():
    """
    This function is responsible for updating the provider configuration and then updating the provider conf details in db and then also sending request to the provider.
    """

    try:
        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate the request data
        errors = conf_schema.validate(data)
        if errors:
            return jsonify({"error": errors}), 400

        # Extract the provider ID and configuration details from the request
        provider_id = data.get("provider_id")
        provider_allowed_ram = data.get("provider_allowed_ram")
        provider_allowed_vcpu = data.get("provider_allowed_vcpu")
        provider_allowed_storage = data.get("provider_allowed_storage")
        provider_allowed_vms = data.get("provider_allowed_vms")
        provider_allowed_networks = data.get("provider_allowed_networks")

        # Send a request to the provider

        # taking out provider_url using provider_id
        provider = provider_details_collection.find_one(
            {"provider_id": provider_id},
            {"_id": 0, "provider_url": 1,"provider_used_ram": 1,"provider_used_vcpu": 1,"provider_used_storage": 1,provider_allowed_vms: 1,provider_allowed_networks: 1}
        )
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        
        # check if the used specs are less than the allowed specs
        if provider["provider_used_ram"] > provider_allowed_ram:
            return jsonify({"error": "More specs(RAM) already being used by clients."}), 400
        if provider["provider_used_vcpu"] > provider_allowed_vcpu:
            return jsonify({"error": "More specs(vcpu) already being used by clients."}), 400
        if provider["provider_used_storage"] > provider_allowed_storage:
            return jsonify({"error": "More specs(storage) already being used by clients."}), 400
        if provider["provider_used_networks"] > provider_allowed_networks:
            return jsonify({"error": "More specs(networks) already being used by clients."}), 400
        if provider["provider_used_vms"] > provider_allowed_vms:
            return jsonify({"error": "More specs(vms) already being used by clients."}), 400
        

        # Extract the provider URL
        provider_url = provider.get("provider_url")

        response=requests.post(
            f"{provider_url}/config/update",
            json={
                "max_ram": provider_allowed_ram,
                "max_cpu": provider_allowed_vcpu,
                "max_disk": provider_allowed_storage,
                "max_vms": provider_allowed_vms,
                "max_networks": provider_allowed_networks,
            }
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to update provider configuration"}), 500
        
        # If the request to the provider was successful, update the provider configuration in the database
        # Update the provider details in the database
        
        provider_conf_collection.update_one(
            {"provider_id": provider_id},
            {
                "$set": {
                    "provider_allowed_ram": provider_allowed_ram,
                    "provider_allowed_vcpu": provider_allowed_vcpu,
                    "provider_allowed_storage": provider_allowed_storage,
                    "provider_allowed_vms": provider_allowed_vms,
                    "provider_allowed_networks": provider_allowed_networks,
                    "conf_updated_at": datetime.now(),
                }
            },
            upsert=True,
        )

        
        return jsonify({"message": "Provider configuration updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500 
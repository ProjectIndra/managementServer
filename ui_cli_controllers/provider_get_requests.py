from flask import jsonify,request

# internal imports
from models.providers import provider_details_collection , provider_conf_collection
from models.providers import provider_schema, conf_schema
from dbConnection import db
from datetime import datetime

def providers(subpath):
    """
    This function is responsible for returning the telemetries of providers.
    """
    if(subpath=="lists"):
       return providers_lists(request)
    elif(subpath=="details"):
         return providers_details(request)
    elif(subpath=="query"):
        return providers_query(request)
    
def providers_lists(request):
    try:
        providers = provider_details_collection.find(
            { "provider_status": "Active" },
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_id": 1,
                "provider_name": 1,
                "user_id": 1,
                "provider_type": 1,
                "provider_ram_capacity": 1,
                "provider_vcpu_capacity": 1,
                "provider_storage_capacity": 1,
                "provider_rating": 1
            }
        )

        providers_list = list(providers)

        # if providers_list:
            # print(providers_list[0]["provider_updated_at"])  # Fixed key access

        return jsonify({"all_providers": providers_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def providers_details(request):
    """
    This function is responsible
    for returning the details of a given provider.
    """
    try:
        provider_id=request.args.get('provider_id')
        if not provider_id:
            return jsonify({"error": "Provider Selection is required"}), 400
        provider = provider_details_collection.find_one(
            {"provider_id": provider_id},
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_id": 1,
                "provider_name": 1,
                "user_id": 1,
                "provider_type": 1,
                "provider_status": 1,
                "provider_ram_capacity": 1,
                "provider_vcpu_capacity": 1,
                "provider_storage_capacity": 1,
                "provider_vms_capacity": 1,
                "provider_networks_capacity": 1,
                "provider_used_ram": 1,
                "provider_used_vcpu": 1,
                "provider_used_storage": 1,
                "provider_used_vms" :1,
                "provider_used_networks" :1,
                "provider_rating": 1
            }
        )
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        # Fetching the provider configuration details
        provider_conf = provider_conf_collection.find_one(
            {"provider_id": provider_id},
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_allowed_ram": 1,
                "provider_allowed_vcpu": 1,
                "provider_allowed_storage": 1,
                "provider_allowed_vms": 1,
                "provider_allowed_networks": 1
            }
        )
        if not provider_conf:
            return jsonify({"error": "Provider configuration not found"}), 404
        # Merging provider and configuration details
        provider_details = {
            **provider,
            **provider_conf
        }
        # Removing the provider_id from the configuration details
        provider_details.pop("provider_id", None)
        
        return jsonify(provider_details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def providers_query(request):
    """
    This function returns whether the user can create a vm or not with the given requriements for a provider.
    params:- vcpu,ram,storage,provider_id
    """
    try:
        vcpu=request.args.get('vcpu')
        ram=request.args.get('ram')
        storage=request.args.get('storage')
        provider_id=request.args.get('provider_id')
        vm_image_type=request.args.get('vm_image_type')

        # check if at least one of the parameters out of vcpu , ram and storage is provided or not
        if not (vcpu or ram or storage):
            return jsonify({"error": "At least one of vcpu, ram or storage is required"}), 400
        if not provider_id:
            return jsonify({"error": "Provider Selection is required"}), 400
        
        # query the provider details and configuration details and then how much more specs can be used by the client by taking difference of the used and allowed specs

        providers_details=provider_details_collection.find_one(
            {"provider_id": provider_id},
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_used_ram": 1,
                "provider_used_vcpu": 1,
                "provider_used_storage": 1,
                "provider_used_vms": 1,
                "provider_used_networks": 1,
                "provider_status": 1,
            }
        )

        if not providers_details:
            return jsonify({"error": "Provider not found"}), 404
        
        # Fetching the provider configuration details
        provider_conf = provider_conf_collection.find_one(
            {"provider_id": provider_id},
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_allowed_ram": 1,
                "provider_allowed_vcpu": 1,
                "provider_allowed_storage": 1,
                "provider_allowed_vms": 1,
                "provider_allowed_networks": 1
            }
        )
        if not provider_conf:
            return jsonify({"error": "Provider configuration not found"}), 404
        
        # check whether the provider is active or not
        if providers_details["provider_status"]!="Active":
            return jsonify({"error": "Provider is not active"}), 404
        
        # check if the queried specs are less than the difference of the used and allowed specs
        if ram and int(ram) > (int(provider_conf["provider_allowed_ram"]) - int(providers_details["provider_used_ram"])):
            return jsonify({"error": "More specs(RAM) already being used by clients.",
                            "can_create": False
                            }), 200
    
        if vcpu and int(vcpu) > (int(provider_conf["provider_allowed_vcpu"]) - int(providers_details["provider_used_vcpu"])):
            return jsonify({"error": "More specs(vcpu) already being used by clients.",
                            "can_create": False
                            }), 200
        
        if storage and int(storage) > (int(provider_conf["provider_allowed_storage"]) - int(providers_details["provider_used_storage"])):
            return jsonify({"error": "More specs(storage) already being used by clients.",
                            "can_create": False
                            }), 200
        
        return jsonify({"can_create": True}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        

# def providers_createVm(request):
from flask import jsonify,request
from datetime import datetime

# internal imports
from models.providers import provider_details_collection , provider_conf_collection
from models.providers import provider_schema, conf_schema
from models.vmsModel import vm_details_collection
from models.authModels import users_collection

def providers(subpath):
    """
    This function is responsible for returning the telemetries of providers.
    """
    if(subpath=="lists"):
       return providers_lists(request)
    elif(subpath=="details"):
         return providers_details(request)
    else:
        return{"error":"invalid path"}
    
def providers_lists(request):
    try:
        providers = provider_details_collection.find(
            { "provider_status": "active" },
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_id": 1,
                "provider_name": 1,
                "user_id": 1,
                "provider_type": 1,
                "provider_rating": 1,
            }
        )
        print("providers",providers)

        providers_list = list(providers)
        # print(providers_list)

    #    iterate over the providers_list and for each provider_id take out the details of provider_conf collection from the provider_id
        for provider in providers_list:
            provider_conf = provider_conf_collection.find_one(
                {"provider_id": provider["provider_id"]},
                {
                    "_id": 0,  # Exclude MongoDB _id field
                    "provider_allowed_ram": 1,
                    "provider_allowed_vcpu": 1,
                    "provider_allowed_storage": 1,
                    "provider_allowed_vms": 1,
                    "provider_allowed_networks": 1
                }
            )
            if provider_conf:
                # Merging provider and configuration details
                provider.update(provider_conf)


        # if providers_list:
            # print(providers_list[0]["provider_updated_at"])  # Fixed key access
        
        # print(providers_list)

        return jsonify({"all_providers": providers_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# this request is an independent request from the other ones it directly comes from server.py , not from if-else

def get_user_provider_details(user):
    """
    This function is responsible for returning the all the providers of a user.
    """
    try:
        user_id= user.get('user_id')
        providers = provider_details_collection.find(
            { "user_id": user_id },
            {
                "_id": 0,  # Exclude MongoDB _id field
                "provider_id": 1,
                "provider_name": 1,
                "user_id": 1,
                "provider_type": 1,
                "provider_rating": 1
            }
        )

        providers_list = list(providers)
        # print(providers_list)

    #    iterate over the providers_list and for each provider_id take out the details of provider_conf collection from the provider_id
        for provider in providers_list:
            provider_conf = provider_conf_collection.find_one(
                {"provider_id": provider["provider_id"]},
                {
                    "_id": 0,  # Exclude MongoDB _id field
                    "provider_allowed_ram": 1,
                    "provider_allowed_vcpu": 1,
                    "provider_allowed_storage": 1,
                    "provider_allowed_vms": 1,
                    "provider_allowed_networks": 1
                }
            )
            if provider_conf:
                # Merging provider and configuration details
                provider.update(provider_conf)
                # Removing the provider_id from the configuration details
                # provider.pop("provider_id", None)

        return jsonify({"all_providers": providers_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def provider_client_details(user):
    """
    This function is responsible for returning the all the providers of a user.
    """
    try:
        user_id= user.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # print(user_id)
        
        # Fetching all the clients associated with the vms of the provider
        vm_cllients= vm_details_collection.find({"provider_user_id": user_id},{"client_user_id":1})

        # fetching all the clients details 
        client_details_list=[]
        for vm_client in vm_cllients:
            client_user_id=vm_client.get("client_user_id")
            client_details_list.append(
                users_collection.find_one({"user_id": client_user_id},{"_id":0,"password":0,"cli_verification_token":0})
            )
        
        return jsonify({"client_details": client_details_list}), 200
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
    


# def providers_createVm(request):
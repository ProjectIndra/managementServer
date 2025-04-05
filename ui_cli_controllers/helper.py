from flask import request, jsonify
import requests
import time
from datetime import datetime
import uuid

# internal imports
from ui_cli_controllers import wg
from provider_controllers import telemetry
from models.vmsModel import vm_details_collection, vm_status_collection
from models.providers import provider_details_collection, provider_conf_collection

def providers_query_helper(request):
    """
    This function returns whether the user can create a vm or not with the given requriements for a provider.
    params:- vcpu,ram,storage,provider_id
    """
    try:
        data=request.get_json()

        vcpu=data.get('vcpu')
        ram=data.get('ram')
        storage=data.get('storage')
        provider_id=data.get('provider_id')
        vm_image_type=data.get('vm_image')

        # print(data)

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
        if providers_details["provider_status"]!="active":
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
        


# properly handle the response throughout the status code
def helper_vm_creation(request,client_user_id):
    """
    This is a helper function responsible for creating a new VM
    """
    try:
        data = request.get_json()

        print(data)
        # provider_url = 'https://pet-muskox-honestly.ngrok-free.app'
        vm_name= data.get('vm_name')
        vcpus = data.get('vcpus', 2)
        ram = data.get('ram', 2048)
        storage = data.get('storage', 20)
        provider_user_id = data.get('provider_user_id')
        # client_user_id = user.get('user_id')
        # provider_name= data.get('provider_name')
        vm_image_type = data.get('vm_image', 'ubuntu')

        provider_id=data.get('provider_id')

        # print(client_user_id)
        # fetching provider url from the DB using provider_id
        provider_response=provider_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1,"management_server_verification_token":1})
        print(provider_response)

        if not provider_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_response.get('provider_url')
        print(provider_url)
        management_server_verification_token=provider_response.get('management_server_verification_token')
        
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        

        network_list = get_network_list(provider_url, management_server_verification_token)

        if "default" not in network_list.get('active_networks', []) and "default" not in network_list.get('inactive_networks', []):
            create_default_network(provider_url, management_server_verification_token)
        elif "default" in network_list.get('inactive_networks', []):
            activate_default_network(provider_url, management_server_verification_token)
        
        vm_data = {
            "name": vm_name,
            "vcpus": vcpus,
            "memory": ram,
            "storage": storage,
            "image": vm_image_type,
            "qvm_path": "./images/avinash.qcow2",
        }
        
        vm_response = create_vm(provider_url, vm_data, management_server_verification_token)
        vm_response_json = vm_response.json()

        print(vm_response_json)
        
        wireguard_response = wg.setup_wireguard(
            provider_url, data,management_server_verification_token
        )

        vm_id=str(uuid.uuid4())
        # inserting vm details in the db
        vm_details = {
            "provider_user_id": provider_user_id,
            "client_user_id": client_user_id,
            # generating uuid for vm_id
            "vm_id":vm_id,
            "vm_name": vm_name,
            # generating unique string as like uuid for internal_vm_name
            "internal_vm_name": f"{vm_name}-{str(uuid.uuid4())}",
            "provider_id": provider_id,
            "ram": ram,
            "vcpu": vcpus,
            "storage": storage,
            "vm_image_type":vm_image_type,
            "vm_creation_time": str(datetime.now()),
            "wireguard_ip": wireguard_response.get('ip'),
            "wireguard_public_key": wireguard_response.get('public_key'),
            "wireguard_status": True,
        }
        vm_details_collection.insert_one(vm_details)
        # inserting vm status in the db
        vm_status = {
            "vm_id": vm_id,
            "vm_name": vm_name,
            "status": "active",
            "provider_id": provider_id,
            "vm_deleted": False,
            "vm_deleted_at": None
        }
        vm_status_collection.insert_one(vm_status)


        return jsonify({
            "message": "Congrats, VM is successfully created",
            "vm_public_key": wireguard_response.get('public_key')
        }), 200
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500


def get_network_list(provider_url, management_server_verification_token):
    """
    Fetches the list of networks from the provider.
    """
    headers = {
        'authorization': management_server_verification_token
    }
    response = requests.get(f"{provider_url}/network/list", headers=headers)
    return response.json()

def create_default_network(provider_url, management_server_verification_token):
    """
    Creates a default network if it doesn't exist.
    """
    headers = {
        'authorization': management_server_verification_token
    }

    network_data = {
        "name": "default",
        "bridgeName": "virbr1",
        "forwardMode": "nat",
        "ipAddress": "192.168.122.1",
        "ipRangeStart": "192.168.122.100",
        "ipRangeEnd": "192.168.122.200",
        "netMask": "255.255.255.0"
    }
    return requests.post(f"{provider_url}/network/create", json=network_data, headers=headers)

def activate_default_network(provider_url, management_server_verification_token):
    """
    Activates the default network if it exists but is inactive.
    """
    headers = {
        'authorization': management_server_verification_token
    }
    return requests.post(f"{provider_url}/network/activate", json={"name": "default"}, headers=headers)

def create_vm(provider_url, vm_data, management_server_verification_token):
    """
    Creates a new VM on the provider.
    """
    headers = {
        'authorization': management_server_verification_token
    }
    return requests.post(f"{provider_url}/vm/create_qvm", json=vm_data, headers=headers)

def helper_activate_vm(provider_id, vm_id):
    """
    helper function to activate existing inactive VM 
    params-vm_name,provider_id
    """

    try:

        # fetching provider url from the DB using provider_id
        provider_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_response.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        management_server_verification_token=provider_response.get('management_server_verification_token')
        

        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        headers = {
            'authorization': management_server_verification_token
        }

        activate_vm_response=requests.post(f"{provider_url}/vm/activate",json={"name":internal_vm_name},headers=headers)
        # print(activate_vm_response)
        # update status in the db
        vm_status_collection.update_one(
            {"vm_id": vm_id},
            {"$set": {"status": "active"}}
        )

        return activate_vm_response.content, activate_vm_response.status_code, activate_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500


def helper_deactivate_vm(provider_id, vm_id):
     # fetching provider url from the DB using provider_id

    # provider_url="https://pet-muskox-honestly.ngrok-free.app"

    try:

        # fetching provider url from the DB using provider_id
        provider_url_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        management_server_verification_token=provider_url_response.get('management_server_verification_token')
        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        headers = {
            'authorization': management_server_verification_token
        }

        deactivate_vm_response=requests.post(f"{provider_url}/vm/deactivate",json={"name":internal_vm_name},headers=headers)
        # print(deactivate_vm_response)
        # update in the db
        vm_status_collection.update_one(
            {"vm_id": vm_id},
            {"$set": {"status": "inactive"}}
        )

        return deactivate_vm_response.content, deactivate_vm_response.status_code, deactivate_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500
  

def helper_delete_vm(provider_id,vm_id):
    """
    helper function to delete inactivated vms
    """
    # fetching provider url from the DB using provider_id

    # provider_url="https://pet-muskox-honestly.ngrok-free.app"

    try:

        # fetching provider url from the DB using provider_id
        provider_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_response.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        management_server_verification_token=provider_response.get('management_server_verification_token')
        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        headers = {
            'authorization': management_server_verification_token
        }

        delete_vm_response=requests.post(f"{provider_url}/vm/delete",json={"name":internal_vm_name},headers=headers)
        # print(delete_vm_response)
        # update status in the db
        vm_status_collection.update_one(
            {"vm_id": vm_id},
            {"$set": {"status": "deleted"}}
        )
        return delete_vm_response.content, delete_vm_response.status_code, delete_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500
 
from flask import request, jsonify
import requests
import time

# internal imports
from ui_cli_controllers import wg
from provider_controllers import telemetry
from models.vmsModel import vm_details_collection, vm_status_collection


def helper_vm_creation(request):
    """
    This is a helper function responsible for creating a new VM
    """
    try:
        data = request.get_json()
        # provider_url = 'https://pet-muskox-honestly.ngrok-free.app'
        
        vm_name = data.get('vm_name', 'new-vm')
        provider_id=data.get('provider_id','f8c52abb-bfa5-44dc-8496-0b0a2fb5c394')

        # fetching provider url from the DB using provider_id
        provider_url_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        

        vm_data = {
            "name": vm_name,
            "vcpus": data.get('vcpus'),
            "memory": data.get('ram'),
            "storage": data.get('storage'),
            "image": data.get('vm_image'),
            "qvm_path": "/var/lib/libvirt/images/avinash.qcow2",
        }

        network_list = get_network_list(provider_url)
        if "default" not in network_list.get('active_networks', []) and "default" not in network_list.get('inactive_networks', []):
            create_default_network(provider_url)
        elif "default" in network_list.get('inactive_networks', []):
            activate_default_network(provider_url)
        
        vm_response = create_vm(provider_url, vm_data)
        vm_response_json = vm_response.json()

        
        wireguard_response = wg.setup_wireguard(
            provider_url, data
        )



        return jsonify({
            "message": "Congrats, VM is successfully created",
            "vm_public_key": wireguard_response.get('public_key')
        }), 200
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500


def get_network_list(provider_url):
    response = requests.get(f'{provider_url}/network/list')
    return response.json()

def create_default_network(provider_url):
    network_data = {
        "name": "default",
        "bridgeName": "virbr1",
        "forwardMode": "nat",
        "ipAddress": "192.168.122.1",
        "ipRangeStart": "192.168.122.100",
        "ipRangeEnd": "192.168.122.200",
        "netMask": "255.255.255.0"
    }
    return requests.post(f"{provider_url}/network/create", json=network_data)

def activate_default_network(provider_url):
    return requests.post(f"{provider_url}/network/activate", json={"name": "default"})

def create_vm(provider_url, vm_data):
    return requests.post(f"{provider_url}/vm/create_qvm", json=vm_data)

def helper_activate_vm(provider_id, vm_id):
    """
    helper function to activate existing inactive VM 
    params-vm_name,provider_id
    """

    try:

        # fetching provider url from the DB using provider_id
        provider_url_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        activate_vm_response=requests.post(f"{provider_url}/vm/activate",json={"name":internal_vm_name})
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
        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        deactivate_vm_response=requests.post(f"{provider_url}/vm/deactivate",json={"name":internal_vm_name})
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
        provider_url_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        # fetching vm_name from the db using vm_id
        internal_vm_name_response=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1})
        if not internal_vm_name_response:
            return jsonify({"error": "VM not found"}), 404
        internal_vm_name=internal_vm_name_response.get('internal_vm_name')

        delete_vm_response=requests.post(f"{provider_url}/vm/delete",json={"name":internal_vm_name})
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
 
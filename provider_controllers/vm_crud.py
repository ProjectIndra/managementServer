from flask import request, jsonify
import requests
import time

# internal imports
from cli_controllers import wg
from provider_controllers import telemetry

def vm_creation():
    """
    This function is responsible for creating new a VM
    """
    try:
        return helper_vm_creation(request)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def helper_vm_creation(request):
    """
    This is a helper function responsible for creating a new VM
    """
    try:
        data = request.get_json()
        provider_url = 'https://pet-muskox-honestly.ngrok-free.app'
        
        vm_name = data.get('vm_name', 'new-vm')
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



# activating existing inactive VM

def activate_vm():
    """
    activating existing inactive VM
    """
    data=request.get_json()
    print(data)
    vm_name=data.get('vm_name','new-vm')
    provider_id=data.get('provider_id',123)
    return helper_activate_vm(provider_id, vm_name)


def helper_activate_vm(provider_id, vm_name):
    """
    helper function to activate existing inactive VM 
    params-vm_name,provider_id
    """
     # fetching provider url from the DB using provider_id

    provider_url="https://pet-muskox-honestly.ngrok-free.app"

    try:
        activate_vm_response=requests.post(f"{provider_url}/vm/activate",json={"name":vm_name})
        # print(activate_vm_response)
        return activate_vm_response.content, activate_vm_response.status_code, activate_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500

# deactivating activated vms
def deactivate_vm():
    """
    deactivating activated vms{params-vm_name,provider_id}
    """
    data=request.get_json()
    print(data)
    vm_name=data.get('vm_name','new-vm')
    provider_id=data.get('provider_id',123)
    return helper_deactivate_vm(provider_id, vm_name)

def helper_deactivate_vm(provider_id, vm_name):
     # fetching provider url from the DB using provider_id

    provider_url="https://pet-muskox-honestly.ngrok-free.app"

    try:
        deactivate_vm_response=requests.post(f"{provider_url}/vm/deactivate",json={"name":vm_name})
        # print(deactivate_vm_response)
        return deactivate_vm_response.content, deactivate_vm_response.status_code, deactivate_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500
    
# deleting inactivated vms
def delete_vm():
    """
    deleting inactivated vms{params-vm_name,provider_id}
    """
    data=request.get_json()
    print(data)
    vm_name=data.get('vm_name','new-vm')
    provider_id=data.get('provider_id',123)
    return helper_delete_vm(provider_id, vm_name)

    
def helper_delete_vm(provider_id,vm_name):
    """
    helper function to delete inactivated vms
    """
    # fetching provider url from the DB using provider_id

    provider_url="https://pet-muskox-honestly.ngrok-free.app"

    try:
        delete_vm_response=requests.post(f"{provider_url}/vm/delete",json={"name":vm_name})
        # print(delete_vm_response)
        return delete_vm_response.content, delete_vm_response.status_code, delete_vm_response.headers.items()
    
    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500
    
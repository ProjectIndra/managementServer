from flask import request, jsonify
import requests

from provider_controllers import telemetry

def vm_creation():
    data = request.get_json()
    vm_name = data.get('vm_name', 'new-vm')
    vcpus = data.get('vcpus')
    ram = data.get('ram')
    vm_image = data.get('vm_image')
    provider_id = data.get('provider_id')
    client_id = data.get('client_id')
    remarks = data.get('remarks')

    print(data)

    # Hardcoded provider URL
    provider_url = 'https://pet-muskox-honestly.ngrok-free.app'

    # networkList_response=requests.get(f'{provider_url}/network/list')
    # networkList_response_json=networkList_response.json()
    # print(networkList_response.json())

    # if "default" not in networkList_response_json.get('networks'):
    #     print("hii")
    #     network_data = {
    #         "name": "default",
    #         "bridgeName": "virbr1",
    #         "forwardMode": "nat",
    #         "ipAddress": "192.168.122.1",
    #         "ipRangeStart": "192.168.122.100",
    #         "ipRangeEnd": "192.168.122.200",
    #         "netMask": "255.255.255.0"
    #     }

    #     # need to check this if this route is working or not
    #     network_create_response = requests.post(f"{provider_url}/network/create", json=network_data)

    #     print(network_create_response.status_code)
    
    # sending request to create VM

    # vm_data={
    #     "name":vm_name,
    #     "vcpus":vcpus,
    #     "memory":ram,
    #     "qvm_path":"/var/lib/libvirt/images/avinash.qcow2"
    # }

    # vm_create_response=requests.post(f"{provider_url}/vm/create_qvm",json=vm_data)
    # vm_create_response_json=vm_create_response.json()

    # print(vm_create_response_json)

    # check the dhcp ips and if it's there then only setup the wireguard configuration

    dhcp_ip_lists_response=requests.post(f"{provider_url}/vm/ipaddresses", json={"vm_name":vm_name})
    print(dhcp_ip_lists_response.json())



    return jsonify({"message": "Congrats VM is successfully created"}), 200


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
    
from flask import request,jsonify
import requests
import time

# internal imports
from models.vmsModel import vm_status_collection, vm_details_collection

def connect_wg():
    """
    This function is responsible for getting the public key of the vm so that the client can connect to the wireguard's vm through it's wireguard.
    """
    try:
        data = request.get_json()

        provider_id=data.get('provider_id','f8c52abb-bfa5-44dc-8496-0b0a2fb5c394')

        # fetching provider url from the DB using provider_id
        provider_url_response=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url.get('provider_url')
        
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        response = setup_wireguard(provider_url, data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def setup_wireguard(provider_url,data,management_server_verification_token=None):

    # first getting ip address of the vm
    vm_id=data.get('vm_id', 123)
    # fetching internal_vm_name from the db using vm_id
    vm_details = vm_details_collection.find_one(
        {"vm_id": vm_id},
        {"_id": 0, "internal_vm_name": 1}
    )
    if not vm_details:
        return jsonify({"error": "VM not found"}), 404
    internal_vm_name = vm_details.get('internal_vm_name')

    dhcp_response = get_dhcp_ip(provider_url, internal_vm_name)
    vm_ip = dhcp_response.get('ip')

    client_public_key=data.get('client_public_key', "Pb1j0VNQYKd7P3W9EfUI3GrzfKDLXv27PCZox3PB5w8="),
    client_endpoint=data.get('client_endpoint', "192.168.0.162:3000")

    # as of now fetching the wireguard_connection_id from the request but later we need to fetch it from the db using the session token
    wireguard_connection_id = data.get('wireguard_connection_id', 123)

    headers = {
        'authorization': management_server_verification_token
    }

    response = requests.post(f"{provider_url}/vm/ssh/setup_wireguard", json={
        "vm_ip": vm_ip,
        "client_id": wireguard_connection_id,
        "client_public_key": client_public_key,
        "client_endpoint": client_endpoint
    },headers=headers)
    
    return response.json()

def get_dhcp_ip(provider_url, internal_vm_name):
    time.sleep(10)  # Wait for DHCP assignment
    response = requests.post(f"{provider_url}/vm/ipaddresses", json={"vm_name": internal_vm_name})
    return response.json()

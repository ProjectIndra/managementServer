from flask import request,jsonify
import requests
import nacl.public
import base64
import os
from dotenv import load_dotenv

# internal imports
from models.vmsModel import vm_status_collection, vm_details_collection
from models.providers import provider_details_collection
from models.authModels import cli_session_collection

load_dotenv()
NETWORK_SERVER = os.getenv("NETWORK_SERVER")

def generate_wireguard_keypair():
    # Generate a new private key (32 random bytes)
    private_key = nacl.public.PrivateKey.generate()

    # Private key bytes
    private_key_bytes = private_key.encode()

    # Corresponding public key
    public_key_bytes = private_key.public_key.encode()

    # Base64 encode like wg expects
    private_key_b64 = base64.standard_b64encode(private_key_bytes).decode('ascii')
    public_key_b64 = base64.standard_b64encode(public_key_bytes).decode('ascii')

    return private_key_b64, public_key_b64


def connect_wg(user):
    """
    This function is responsible for getting the public key of the vm so that the client can connect to the wireguard's vm through it's wireguard.
    """
    try:
        data = request.get_json()

        vm_name=data.get('vm_name','test-vm')
        interface_name=data.get('interface_name','wg0')

        if not vm_name or not interface_name:
            return jsonify({"error": "Missing vm_name or interface_name"}), 400

        user_id=user.get('user_id')
        cli_id=user.get('cli_id')


        # fetching provider_id from the db using user_id and vm_name
        vm_status_details=vm_status_collection.find_one({"vm_name":vm_name,"client_user_id":user_id,"status":'active'})
        if not vm_status_details:
            return jsonify({"error": "VM not found or inactive"}), 404
        
        vm_id=vm_status_details.get('vm_id')

        vm_details=vm_details_collection.find_one({"vm_id":vm_id},{"_id":0,"internal_vm_name":1,"provider_id":1})
        
        provider_id=vm_details.get('provider_id')
        internal_vm_name=vm_details.get('internal_vm_name')

        # fetching provider url from the DB using provider_id
        provider_url_response=provider_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1,"management_server_verification_token":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url_response.get('provider_url')
        management_server_verification_token=provider_url_response.get('management_server_verification_token')        
        
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        # sending the client details to the network server after generating the public key and private key

        client_public_key, client_private_key = generate_wireguard_keypair()

        client_add_peer_response = requests.post(f"{NETWORK_SERVER}/api/addPeer", json={
            "interface_name": interface_name,
            "peer_name": cli_id + "->" + vm_id,
            "public_key": client_public_key,
        })
        print("user_id",client_add_peer_response.json())
        client_add_peer_response_json = client_add_peer_response.json()
        if client_add_peer_response.status_code != 200:
            return jsonify({"error": client_add_peer_response_json.get("error")}), client_add_peer_response.status_code
        
        client_interface_details = client_add_peer_response_json.get("interface_details")

        # sending the vm details to the network server after generating the public key and private key
        
        vm_public_key, vm_private_key = generate_wireguard_keypair()
        vm_add_peer_response = requests.post(f"{NETWORK_SERVER}/api/addPeer", json={
            "interface_name": interface_name,
            "peer_name": vm_id + "->" + cli_id,
            "public_key": vm_public_key,
        })
        vm_add_peer_response_json = vm_add_peer_response.json()
        if vm_add_peer_response.status_code != 200:
            return jsonify({"error": vm_add_peer_response_json.get("error","")}), vm_add_peer_response.status_code
        vm_interface_details = vm_add_peer_response_json.get("interface_details")

        combined_interface_details = {
            "interface_allowed_ips": client_interface_details.get("interface_allowed_ips"),
            "interface_endpoint": client_interface_details.get("interface_endpoint"),
            "interface_name": client_interface_details.get("interface_name"),
            "interface_public_key": client_interface_details.get("interface_public_key"),
            "client_peer_name": client_interface_details.get("peer_name"),
            "client_peer_address": client_interface_details.get("peer_address"),
            "client_peer_public_key": client_interface_details.get("peer_public_key"),
            "client_peer_private_key": client_private_key,
            "vm_peer_name": vm_interface_details.get("peer_name"),
            "vm_peer_address": vm_interface_details.get("peer_address"),
            "vm_peer_public_key": vm_interface_details.get("peer_public_key"),
            "vm_peer_private_key": vm_private_key,
        }

        response = setup_wireguard(provider_url, internal_vm_name,  management_server_verification_token, cli_id, combined_interface_details)

        if response[1] != 200:
            return response
        
        return combined_interface_details, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def setup_wireguard(provider_url, internal_vm_name, management_server_verification_token, cli_id,combined_interface_details):
    """
    This function is responsible for setting up the wireguard connection.
    """

    dhcp_response = get_dhcp_ip(provider_url, internal_vm_name, management_server_verification_token)
    
    vm_ip = dhcp_response.get('ip')

    headers = {
        'authorization': management_server_verification_token
    }

    wireguard_response = requests.post(f"{provider_url}/vm/ssh/setup_wireguard", json={
        "vm_ip": vm_ip,
        "combined_interface_details": combined_interface_details,
    },headers=headers)

    wireguard_response_json = wireguard_response.json()

    if wireguard_response.status_code != 200:
        return jsonify({"error":wireguard_response_json.get("error")}), wireguard_response.status_code

    # adding cli_id in combined_interface_details
    combined_interface_details["cli_id"] = cli_id
    
    # Update the wireguard details of the vm in the database

    # Try to update the existing entry with the same cli_id
    update_result = vm_details_collection.update_one(
        {
            "internal_vm_name": internal_vm_name,
            "combined_interface_details.cli_id": cli_id
        },
        {
            "$set": {
                "combined_interface_details.$": combined_interface_details
            }
        }
    )

    # If cli_id not found, push it as new entry
    if update_result.matched_count == 0:
        vm_details_collection.update_one(
            {"internal_vm_name": internal_vm_name},
            {"$push": {"combined_interface_details": combined_interface_details}}
        )
        
    return wireguard_response_json, 200

def get_dhcp_ip(provider_url, internal_vm_name, management_server_verification_token):

    headers = {
        'authorization': management_server_verification_token
    }

    response = requests.post(f"{provider_url}/vm/ipaddresses", json={"vm_name": internal_vm_name},headers=headers)
    return response.json()

from flask import request,jsonify
import requests
import time

def connect_wg():
    """
    This function is responsible for getting the public key of the vm so that the client can connect to the wireguard's vm through it's wireguard.
    """
    try:
        data = request.get_json()
        provider_url = 'https://pet-muskox-honestly.ngrok-free.app'
        response = setup_wireguard(provider_url, data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def setup_wireguard(provider_url,data):

    # first getting ip address of the vm
    vm_name=data.get('vm_name', 'new-vm')
    dhcp_response = get_dhcp_ip(provider_url, vm_name)
    vm_ip = dhcp_response.get('ip')

    client_public_key=data.get('client_public_key', "Pb1j0VNQYKd7P3W9EfUI3GrzfKDLXv27PCZox3PB5w8="),
    client_endpoint=data.get('client_endpoint', "192.168.0.162:3000")

    # as of now fetching the wireguard_connection_id from the request but later we need to fetch it from the db using the session token
    wireguard_connection_id = data.get('wireguard_connection_id', 123)

    response = requests.post(f"{provider_url}/vm/ssh/setup_wireguard", json={
        "vm_ip": vm_ip,
        "client_id": wireguard_connection_id,
        "client_public_key": client_public_key,
        "client_endpoint": client_endpoint
    })
    return response.json()

def get_dhcp_ip(provider_url, vm_name):
    time.sleep(10)  # Wait for DHCP assignment
    response = requests.post(f"{provider_url}/vm/ipaddresses", json={"vm_name": vm_name})
    return response.json()

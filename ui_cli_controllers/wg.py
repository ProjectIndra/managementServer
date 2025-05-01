from flask import request,jsonify
import requests
import time

# internal imports
from models.vmsModel import vm_status_collection, vm_details_collection
from models.providers import provider_details_collection
from models.authModels import cli_session_collection

def connect_wg(user):
    """
    This function is responsible for getting the public key of the vm so that the client can connect to the wireguard's vm through it's wireguard.
    """
    try:
        data = request.get_json()

        client_public_key=data.get('client_public_key')
        client_endpoint=data.get('client_endpoint')
        vm_name=data.get('vm_name','test-vm')

        if not client_public_key or not client_endpoint or not vm_name:
            return jsonify({"error": "Missing required parameters"}), 400

        # provider_id=data.get('provider_id','f8c52abb-bfa5-44dc-8496-0b0a2fb5c394')
        # cli_id=data.get('cli_id','123')
        # cli_session_token=data.get('cli_session_token','123')

        # # verifying the cli session token along with it's expiry
        # cli_session=cli_session_collection.find_one({"cli_session_token":cli_session_token,"cli_id":cli_id},{"_id":0,"cli_session_token":1,"cli_session_token_expiry_timestamp":1,"user_id":1})
        # if not cli_session:
        #     return jsonify({"error": "Invalid session token"}), 401
        # if cli_session.get('cli_session_token_expiry_timestamp') < time.time():
        #     return jsonify({"error": "Session token expired"}), 401
        
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

        print("user_id",user_id)
        print("vm_details",vm_details)

        # fetching provider url from the DB using provider_id
        provider_url_response=provider_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1,"management_server_verification_token":1})
        if not provider_url_response:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider_url_response.get('provider_url')
        management_server_verification_token=provider_url_response.get('management_server_verification_token')        
        
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        
        response = setup_wireguard(provider_url, internal_vm_name, management_server_verification_token,cli_id, client_public_key, client_endpoint)

        # ({'message': 'WireGuard setup completed successfully', 'public_key': '7exp0J47QFpy/Hc1P4+DmYT32hb7Vy/JtYH5/e1qVBQ=', 'status': 'active', 'wiregaurd_ip': '10.0.0.2/32'}, 200)


        username,password=getImageUsernamePassword(internal_vm_name)
        response[0]['username']=username
        response[0]['password']=password

        if response[1] != 200:
            return response
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def setup_wireguard(provider_url, internal_vm_name, management_server_verification_token, cli_id, client_public_key, client_endpoint):
    """
    This function is responsible for setting up the wireguard connection.
    """

    # # first getting ip address of the vm
    # vm_id=data.get('vm_id', 123)
    # # fetching internal_vm_name from the db using vm_id
    # vm_details = vm_details_collection.find_one(
    #     {"vm_id": vm_id},
    #     {"_id": 0, "internal_vm_name": 1}
    # )
    # if not vm_details:
    #     return jsonify({"error": "VM not found"}), 404
    # internal_vm_name = vm_details.get('internal_vm_name')

    dhcp_response = get_dhcp_ip(provider_url, internal_vm_name, management_server_verification_token)
    print(dhcp_response)
    vm_ip = dhcp_response.get('ip')

    # client_public_key=data.get('client_public_key', "Pb1j0VNQYKd7P3W9EfUI3GrzfKDLXv27PCZox3PB5w8="),
    # client_public_key=data.get('client_public_key')
    # client_endpoint=data.get('client_endpoint', "192.168.0.162:3000")

    print("client_public_key",client_public_key)

    headers = {
        'authorization': management_server_verification_token
    }

    print(vm_ip)

    wireguard_response = requests.post(f"{provider_url}/vm/ssh/setup_wireguard", json={
        "vm_ip": vm_ip,
        "client_id": cli_id,
        "client_public_key": client_public_key,
        "client_endpoint": client_endpoint
    },headers=headers)

    wireguard_response_json = wireguard_response.json()

    if wireguard_response.status_code != 200:
        return jsonify({"error":wireguard_response_json.get("error")}), wireguard_response.status_code
    # Update the wireguard details of the vm in the database

    update_result = vm_details_collection.update_one(
        {
            "internal_vm_name": internal_vm_name,
            "wireguard_connection_details.cli_id": cli_id  # Check if cli_id exists
        },
        {
            "$set": {
                "wireguard_connection_details.$[elem].wireguard_ip": wireguard_response_json.get("wiregaurd_ip"),
                "wireguard_connection_details.$[elem].wireguard_public_key": wireguard_response_json.get("public_key"),
                "wireguard_connection_details.$[elem].wireguard_status": wireguard_response_json.get("status"),
                "wireguard_connection_details.$[elem].wireguard_port": wireguard_response_json.get("wiregaurd_port"),
            }
        },
        array_filters=[
            {"elem.cli_id": cli_id}
        ]
    )

    # If no existing cli_id matched, push as new
    if update_result.matched_count == 0:
        new_connection = {
            "wireguard_ip": wireguard_response_json.get("wiregaurd_ip"),
            "wireguard_public_key": wireguard_response_json.get("public_key"),
            "cli_id": cli_id,
            "wireguard_status": wireguard_response_json.get("status"),
            "wireguard_port": wireguard_response_json.get("wiregaurd_port")
        }

        vm_details_collection.update_one(
            {"internal_vm_name": internal_vm_name},
            {"$push": {"wireguard_connection_details": new_connection}}
        )

        
    return wireguard_response_json, 200

def get_dhcp_ip(provider_url, internal_vm_name, management_server_verification_token):

    headers = {
        'authorization': management_server_verification_token
    }

    response = requests.post(f"{provider_url}/vm/ipaddresses", json={"vm_name": internal_vm_name},headers=headers)
    return response.json()


def getImageUsernamePassword(internal_vm_name):
    """
    This function is responsible for getting the username and password of the vm image.
    """
    # For now returning hardcoded values
    return "avinash","avinash"
from flask import request, jsonify
import requests

from provider_controllers import provider

def vm_creation():
    data = request.get_json()
    vm_name = data.get('vm_name', 'new-vm')
    vcpus = data.get('vcpus')
    ram = data.get('ram')
    vm_image = data.get('vm_image')
    provider_id = data.get('provider_id')
    client_id = data.get('client_id')
    remarks = data.get('remarks')

    # print(data)

    # Hardcoded provider URL
    provider_url = 'https://pet-muskox-honestly.ngrok-free.app'

    networkList_response=requests.get(f'{provider_url}/network/list')
    networkList_response_json=networkList_response.json()
    # print(networkList_response.json())

    if "default" not in networkList_response_json.get('networks'):
        print("hii")
        network_data = {
            "name": "default",
            "bridgeName": "virbr1",
            "forwardMode": "nat",
            "ipAddress": "192.168.122.1",
            "ipRangeStart": "192.168.122.100",
            "ipRangeEnd": "192.168.122.200",
            "netMask": "255.255.255.0"
        }

        # need to check this if this route is working or not
        network_create_response = requests.post(f"{provider_url}/network/create", json=network_data)

        print(network_create_response.status_code)
    
    # sending request to create VM

    vm_data={
        "name":vm_name,
        "vcpus":vcpus,
        "memory":ram,
        "qvm_path":"/var/lib/libvirt/images/avinash.qcow2"
    }

    vm_create_response=requests.post(f"{provider_url}/vm/create_qvm",json=vm_data)
    vm_create_response_json=vm_create_response.json()

    print(vm_create_response_json)


    return jsonify({"message": "Congrats VM is successfully created"}), 200

    
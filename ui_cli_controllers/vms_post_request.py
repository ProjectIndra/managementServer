from flask import jsonify,request

from ui_cli_controllers import helper

# internal imports
from provider_controllers import vm_crud
from ui_cli_controllers import provider_get_requests

def launchVm():
    """
    This function is responsible
    for launching the vm with the given specs and other details.
    """
    try:
        # first query the provider that whether it is possible to create a vm with the given specs
        response=provider_get_requests.providers_query(request)
        if response[1]!=200:
            return response
        if response[1]==200:
            print(response[0].get_json())
            if response[0].get_json().get('can_create',False)==False:
                return jsonify({"error": "Cannot create VM with the given specs"}), 500
            
        
        # create the vm with the given specs
        response=helper.helper_vm_creation(request)

        # if response[1]==200:
        print("launch-vm")
        if True:
            # return response[0], 200
            return jsonify({"message": "VM is successfully created"}), 200
        else:
            return jsonify({"error": "Failed to create the VM"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to create the VM"}), 500
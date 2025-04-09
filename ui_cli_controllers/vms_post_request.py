from flask import jsonify,request


# internal imports
from ui_cli_controllers import helper
from provider_controllers import vm_crud
from ui_cli_controllers import provider_post_requests


def launchVm(user):
    """
    This function is responsible
    for launching the vm with the given specs and other details.
    """
    try:
        # first query the provider that whether it is possible to create a vm with the given specs
        response=helper.providers_query_helper(request)
        if response[1]!=200:
            return response
        if response[1]==200:
            # print(response[0].get_json())
            if response[0].get_json().get('can_create',False)==False:
                return jsonify({"error": "Cannot create VM with the given specs"}), 500
        
        # print(user)
        client_user_id=user.get('user_id')
        # create the vm with the given specs
        response=helper.helper_vm_creation(request,client_user_id)

        # print("launch-vm")
        # if True:
        #     return jsonify({"message": "VM is successfully created"}), 200
        if response[1]==200:
            return response[0], 200
        else:
            print(response[0].get_json())
            return jsonify(response[0].get_json()), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to create the VM"}), 500
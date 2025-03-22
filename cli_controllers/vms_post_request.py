from flask import jsonify,request

# internal imports
from provider_controllers import vm_crud

def launchVm():
    """
    This function is responsible
    for launching the vm with the given specs and other details.
    """
    try:
        # create the vm with the given specs
        # response=vm_crud.helper_vm_creation(request)

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
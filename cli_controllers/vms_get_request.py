from flask import jsonify, request

# internal imports
from provider_controllers import vm_crud
from cli_controllers import provider_get_requests

def vmStatus(subpath):
    """
    This function is responsible for returning the telemetries of the VMs.
    """
    try:
        if subpath == "allActiveVms":
            return vmStatus_allActiveVms()
        elif subpath == "allVms":
            return vmStatus_allVms()
        elif subpath == "start":
            return vmStatus_vm_start(request)
        elif subpath == "stop":
            return vmStatus_vm_stop(request)
        elif subpath == "remove":
            return vmStatus_vm_remove(request)
        elif subpath == "forceRemove":
            return vmStatus_vm_forceRemove(request)
        elif subpath == "create/verify_provider":
            return vmCreate_verifyprovider(request)
        elif subpath == "create/verify_specs":
            return vmCreate_verifyspecs(request)
        else:
            return jsonify({"error": "Invalid subpath"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_allActiveVms():
    """
    This function is responsible
    for returning the lists of all the active vms along with their wireguard connection status.
    """
    try:
        return jsonify(
            {
                "active_vms": [
                    {
                        "vm_id": "vm-1",
                        "vm_name": "Ubuntu",
                        "wireguard_ip": "10.24.37.4",
                        "wireguard_status": False,
                        "provider_id": "1",
                        "provider_name": "provider-1",
                    },
                    {
                        "vm_id": "vm-2",
                        "vm_name": "Ubuntu",
                        "wireguard_ip": "12.344.23.4",
                        "wireguard_status": True,
                        "provider_id": "1",
                        "provider_name": "provider-1",
                    }
                ]
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_allVms():
    """
    This function is responsible
    for returning the lists of all the inactive vms.
    """
    try:
        return jsonify(
            {
                "all_vms": [
                    {
                        "vm_id": "reddy-vm-1",
                        "vm_name": "Ubuntu",
                        "wireguard_ip": "10.24.37.4",
                        "provider_id": "1",
                        "provider_name": "provider-1",
                    },
                    {
                        "vm_id": "vm-2",
                        "vm_name": "Ubuntu",
                        "wireguard_ip": "12.344.23.4",
                        "provider_id": "1",
                        "provider_name": "provider-1",
                    }
                ]
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_start(request):
    """
    This function is responsible for starting an inactive vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        vm_name = "Ubuntu"
        provider_id = "123"
        response = vm_crud.helper_activate_vm(provider_id, vm_name)

        if response[1] == 200:
            return jsonify({"message": f"VM {vm_id} is successfully started"}), 200
        else:
            return jsonify({"error": "Failed to start VM"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_stop(request):
    """
    This function is responsible for stopping an active vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        vm_name = "Ubuntu"
        provider_id = "123"
        response = vm_crud.helper_deactivate_vm(provider_id, vm_name)

        if response[1] == 200:
            return jsonify({"message": f"VM {vm_id} is successfully stopped"}), 200
        else:
            return jsonify({"error": "Failed to stop the VM"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_remove(request):
    """
    This function is responsible
    for removing an inactive vm with the vm_id/vm_name.
    """
    try:
        is_vm_active = False
        vm_id = request.args.get('vm_id',1234)
        if is_vm_active:
            return jsonify({"error": "VM is still active. To forcefully inactive it try with command 'rm -f' or else first deactivate the vm"}), 500
        else:
            vm_name = "Ubuntu"
            provider_id = "123"
            response = vm_crud.helper_delete_vm(provider_id, vm_name)

            if response[1] == 200:
                return jsonify({"message": f"Inactive-VM {vm_id} is successfully deleted"}), 200
            else:
                return jsonify({"error": "Failed to delete the VM"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_forceRemove(request):
    """
    This function is responsible for forcefully removing an active vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        vm_name = "Ubuntu"
        provider_id = "123"
        response = vm_crud.helper_delete_vm(provider_id, vm_name)

        if response[1] == 200:
            return jsonify({"message": "VM is successfully force deleted"}), 200
        else:
            return jsonify({"error": "Failed to force delete VM"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmCreate_verifyprovider(request):
    """
    This function is responsible for verifying the provider creating the vm.
    """
    try:
        provider_id = request.args.get('provider_id')
        active_providers, status_code = provider_get_requests.providers_lists(request)  # Unpack the tuple
        active_providers_list = active_providers.get_json().get('active_providers')  # Use get_json()

        provider_ids = [provider.get('provider_id') for provider in active_providers_list]

        if status_code != 200:
            return jsonify({"error": "Failed to verify the provider"}), 500


        if provider_id in provider_ids:
            return jsonify({"message": "Provider is active"}), 200
        else:
            return jsonify({"error": "Provider is inactive"}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


def vmCreate_verifyspecs(request):
    """
    This function is responsible
    for verifying the specs of the vm before creating it.
    """
    try:
        response = provider_get_requests.providers_query(request)
        # return jsonify({"can_create": response.json.get('can_create')}), 200 if response.json.get('can_create') else 500
        if response[1] != 200:
            return jsonify({"error": "Failed to verify the specs"}), 500
        
        if response[0].get_json().get('can_create'):
             return jsonify({"message": "VM can be created"}), 200
        else:
            return jsonify({"error": "VM can't be created"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

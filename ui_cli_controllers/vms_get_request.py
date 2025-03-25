from flask import jsonify,request

# internal imports
from provider_controllers import vm_crud
from ui_cli_controllers import provider_get_requests
from ui_cli_controllers.helper import helper_activate_vm
from models.vmsModel import vm_status_collection, vm_details_collection

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
    Fetch and return the list of all VMs from the database.
    """
    # try:
    #     all_vms = list(vm_status_collection.find({}, {"_id": 0}))  # Exclude MongoDB's _id field
    #     return jsonify({"all_vms": all_vms}), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500
    # try:
    #     vm_status_data = [
    #         {
    #             "user_id": f"user-{i}",
    #             "vm_id": f"vm-{i}",
    #             "vm_name": "Ubuntu" if i % 2 == 0 else "Windows",
    #             "status": "active" if i % 2 == 0 else "inactive"
    #         }
    #         for i in range(1, 11)
    #     ]
        
    #     vm_details_data = [
    #         {
    #             "user_id": f"user-{i}",
    #             "vm_id": f"vm-{i}",
    #             "vm_name": "Ubuntu" if i % 2 == 0 else "Windows",
    #             "provider_id": str(i % 3 + 1),
    #             "provider_name": f"provider-{i % 3 + 1}",
    #             "vcpu": str(2 + (i % 4)),
    #             "ram": f"{4 + (i % 4)}GB",
    #             "storage": f"{50 + (i % 5) * 10}GB",
    #             "wireguard_ip": f"10.24.{i}.4",
    #             "wireguard_public_key": f"key-{i}",
    #             "wireguard_endpoint": f"endpoint-{i}",
    #             "internal_vm_name": f"internal-vm-{i}"
    #         }
    #         for i in range(1, 11)
    #     ]

    #     vm_status_collection.insert_many(vm_status_data)
    #     vm_details_collection.insert_many(vm_details_data)
        
    #     return {"message": "Dummy VM data inserted successfully"}, 201
    # except Exception as e:
    #     return {"error": str(e)}, 500
    try:
        all_vms = []
        vm_status_list = list(vm_status_collection.find({}, {"_id": 0, "user_id": 1, "vm_id": 1, "vm_name": 1, "status": 1}))
        
        for vm in vm_status_list:
            vm_details = vm_details_collection.find_one(
                {"vm_id": vm["vm_id"]},
                {"_id": 0, "provider_id": 1, "provider_name": 1, "vcpu": 1, "ram": 1, "storage": 1, "wireguard_ip": 1, "wireguard_public_key": 1, "wireguard_endpoint": 1, }
            )
            
            if vm_details:
                vm.update(vm_details)
            
            all_vms.append(vm)
        
        return {"all_vms": all_vms}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def vmStatus_vm_start(request):
    """
    This function is responsible for starting an inactive vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        vm_name = "Ubuntu" # Hardcoded for now , need to fetch from db using vm_id , it's the internal name of the vm
        # fetching internal_vm_name from db using vm_id
        
        provider_id = request.args.get('provider_id')
        print("vm_id",vm_id)
        print("provider_id",provider_id)
        response = helper_activate_vm(provider_id, vm_name)

        # return {"error": f"VM {vm_id} is successfully started"}, 400

        if response[1] == 200:
            return jsonify({"message": f"VM {vm_id} is successfully started"}), 400
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
        vm_name = "Ubuntu" # Hardcoded for now , need to fetch from db using vm_id , it's the internal name of the vm
        provider_id = request.args.get('provider_id')
        # print(vm_id)
        # print(provider_id)
        # print(request.args)
        response = vm_crud.helper_deactivate_vm(provider_id, vm_name)
        # return {"error": f"VM {vm_id} is successfully stopped"}, 400

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
        vm_id = request.args.get('vm_id',1234)
        is_vm_active = False    #need to fetch from db using vm_id if it's active or not
        provider_id = request.args.get('provider_id',123)
        # print(vm_id)
        # print(provider_id)

        return jsonify({"message": "Done"}), 200
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

from flask import jsonify,request
from datetime import datetime as dateTime
from werkzeug.datastructures import ImmutableMultiDict


# internal imports
# from provider_controllers import vm_crud
from ui_cli_controllers import provider_get_requests
from ui_cli_controllers.helper import helper_activate_vm
from models.vmsModel import vm_status_collection, vm_details_collection
from ui_cli_controllers import helper

def vmStatus(subpath,user):
    """
    This function is responsible for returning the telemetries of the VMs.
    """
    try:
        user_id = user.get('user_id')
        if subpath == "allActiveVms":
            return vmStatus_allActiveVms(user_id)
        elif subpath == "allVms":
            return vmStatus_allVms(user_id)
        elif subpath == "start":
            return vmStatus_vm_start(request,user_id)
        elif subpath == "startCLI":      #this is called from cli to remove any vm
            responseRequest=modifyrequest(request,user_id) #modify the request to add the vm_id and provider_id
            if responseRequest[1] != 200:
                return responseRequest
            return vmStatus_vm_start(responseRequest[0],user_id)
        elif subpath == "stop":
            return vmStatus_vm_stop(request,user_id)
        elif subpath == "stopCLI":       #this is called from cli to remove any vm
            responseRequest=modifyrequest(request,user_id) #modify the request to add the vm_id and provider_id
            if responseRequest[1] != 200:
                return responseRequest
            return vmStatus_vm_stop(responseRequest[0],user_id)
        elif subpath == "remove":
            return vmStatus_vm_remove(request,user_id)
        elif subpath == "removeCLI":    #this is called from cli to remove any vm
            responseRequest=modifyrequest(request,user_id) #modify the request to add the vm_id and provider_id
            if responseRequest[1] != 200:
                return responseRequest
            return vmStatus_vm_remove(responseRequest[0],user_id)
        
        elif subpath == "forceRemoveCLI":
            responseRequest=modifyrequest(request,user_id)
            if responseRequest[1] != 200:
                return responseRequest
            return vmStatus_vm_forceRemove(responseRequest[0],user_id)
        # elif subpath == "create/verify_provider":
        #     return vmCreate_verifyprovider(request)
        # elif subpath == "create/verify_specs":
        #     return vmCreate_verifyspecs(request)
        else:
            return jsonify({"error": "Invalid subpath"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def modifyrequest(req, user_id):
    try:
        vm_name = req.args.get('vm_name')
        vm_details = vm_status_collection.find_one(
            {"vm_name": vm_name, "vm_deleted":False, "client_user_id": user_id},
            {"_id": 0, "vm_id": 1, "provider_id": 1}
        )
    
        if not vm_details:
            print("vm not found")
            return jsonify({"error": "VM not found"}), 404

        new_args = req.args.to_dict()
        new_args['vm_id'] = vm_details.get('vm_id')
        new_args['provider_id'] = vm_details.get('provider_id')


        # Wrap in new ImmutableMultiDict to simulate a modified request
        req.args = ImmutableMultiDict(new_args)
        
        return req,200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def vmStatus_allActiveVms(user_id):
    """
    Fetch and return the list of all active VMs for a specific user along with their WireGuard connection status.
    """
    try:
        print("user_id",user_id)
        active_vms = []

        query = {
            "client_user_id": user_id
        }

        vm_details_list = list(vm_details_collection.find(
            query,
            {
                "_id": 0,
                "vm_id": 1,
                "vm_name": 1,
                "provider_id": 1,
                "provider_name": 1,
                "wireguard_ip": 1,
                "wireguard_public_key": 1,
                "wireguard_status": 1
            }
        ))

        for vm in vm_details_list:
            status_info = vm_status_collection.find_one(
                {"vm_id": vm["vm_id"], "status": "active"},
                {"_id": 0, "status": 1}
            )

            if status_info:
                active_vms.append(vm)

        return jsonify({"active_vms": active_vms}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def vmStatus_allVms(user_id):
    """
    Fetch and return the list of all VMs from the database.
    """
    try:
        
        # vm_details_collection.update_many({"user_id":user_id}, {"$set": {"wireguard_status": "inactive","vm_created_at":dateTime.now()}})

        all_vms = []

        search_query=request.args.get('vm_name', None)

        query={"client_user_id": user_id}
        if search_query:
            query['vm_name'] = { "$regex": f"^{search_query}", "$options": "i" }
            


        # Step 1: Get all VMs for the user from vm_details_collection
        vm_details_list = list(vm_details_collection.find(
            query,
            {
                "_id": 0,
                "vm_id": 1,
                "vm_name": 1,
                "provider_id": 1,
                "provider_name": 1,
                "vcpu": 1,
                "ram": 1,
                "storage": 1,
                "vm_image_type": 1,
                "wireguard_connection_details": 1,
                "vm_created_at": 1
            }
        ))

        # Step 2: For each VM, get its status from vm_status_collection
        for vm in vm_details_list:
            status_info = vm_status_collection.find_one(
            {"vm_id": vm["vm_id"]},
            {"_id": 0, "status": 1, "vm_deleted": 1, "vm_deleted_at": 1}
    )

            if status_info:
                if status_info.get("status") in ["active", "inactive"]:
                    vm.update(status_info)
                    all_vms.append(vm)
            else:
                pass
        
        return {"all_vms": all_vms}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def vmStatus_vm_start(request,user_id):
    """
    This function is responsible for starting an inactive vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        
        provider_id = request.args.get('provider_id')
        # print("vm_id",vm_id)
        # print("provider_id",provider_id)
        response = helper_activate_vm(provider_id, vm_id,user_id)

        
        if response.status_code == 200:
            vm_status_collection.update_one(
            {"vm_id": vm_id},
            {"$set": {"status": "active"}}
        )
            return jsonify({"message": f"VM is successfully started"}), 200
        elif response.status_code == 404:
            return jsonify({"error":"Provider where the VM is not reachable.Sorry for the inconvenience"}),500
        else:
            return response.json(), 400
    except Exception as e:
        print("error",e)
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_stop(request,user_id):
    """
    This function is responsible for stopping an active vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        provider_id = request.args.get('provider_id')
        # print(vm_id)
        # print(provider_id)
        # print(request.args)
        response = helper.helper_deactivate_vm(provider_id, vm_id, user_id)
        # return {"error": f"VM {vm_id} is successfully stopped"}, 400

        if response[1] == 200:
            # update in the db
            vm_status_collection.update_one(
            {"vm_id": vm_id},
            {"$set": {"status": "inactive"}}
        )
            return jsonify({"message": f"VM is successfully stopped"}), 200
        elif response[1] == 404:
            return jsonify({"error":"Provider where the VM is not reachable.Sorry for the inconvenience"}),500
        else:
            return response[0], 400
    except Exception as e:
        print("error",e)
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_remove(request,user_id):
    """
    This function is responsible
    for removing an inactive vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id',1234)
        # fetch from db using vm_id if it's active or not
        vm_status = vm_status_collection.find_one({"vm_id": vm_id,"client_user_id":user_id}, {"_id": 0, "status": 1,"provider_id":1})
        if not vm_status:
            return jsonify({"error": "VM not found"}), 404
        is_vm_active = vm_status.get('status') == 'active'

        provider_id = request.args.get('provider_id') 
        # print(vm_id)
        # print(provider_id)

        # return jsonify({"message": "Done"}), 200
        if is_vm_active:
            return jsonify({"error": "VM is still active. To forcefully inactive it try with command 'rm -f' or else first deactivate the vm"}), 500
        else:
            response = helper.helper_delete_vm(provider_id, vm_id,user_id)

            if response[1] == 200:
                return jsonify({"message": f"VM is successfully deleted"}), 200
            elif response[1] == 404:
                return jsonify({"error":"Provider where the VM is not reachable.Sorry for the inconvenience"}),500
            else:
                return jsonify({"error": "Failed to delete the VM"}), 400
    except Exception as e:
        print("error",e)
        return jsonify({"error": str(e)}), 500

def vmStatus_vm_forceRemove(request,user_id):
    """
    This function is responsible for forcefully removing an active vm with the vm_id/vm_name.
    """
    try:
        vm_id = request.args.get('vm_id')
        provider_id = request.args.get('provider_id')
        # fetch provider_id from db using vm_id
        vm_status = vm_status_collection.find_one({"vm_id": vm_id,"client_user_id":user_id}, {"_id": 0, "status": 1,"provider_id":1})
        if not vm_status:
            return jsonify({"error": "VM not found"}), 404
        
        response = helper.helper_delete_vm(provider_id, vm_id,user_id)

        if response[1] == 200:
            return jsonify({"message": "VM is successfully force deleted"}), 200
        elif response[1] == 404:
            return jsonify({"error":response[0].json.get('error')}),500
        else:
            return jsonify({"error": "Failed to force delete VM"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# def vmCreate_verifyprovider(request):
#     """
#     This function is responsible for verifying the provider before creating the vm.
#     """
#     try:
#         provider_id = request.args.get('provider_id')
#         active_providers, status_code = provider_get_requests.providers_lists(request)  # Unpack the tuple
#         active_providers_list = active_providers.get_json().get('active_providers')  # Use get_json()

#         provider_ids = [provider.get('provider_id') for provider in active_providers_list]

#         if status_code != 200:
#             return jsonify({"error": "Failed to verify the provider"}), 500


#         if provider_id in provider_ids:
#             return jsonify({"message": "Provider is active"}), 200
#         else:
#             return jsonify({"error": "Provider is inactive"}), 400
#     except Exception as e:
#         print(e)
#         return jsonify({"error": str(e)}), 500


# def vmCreate_verifyspecs(request):
#     """
#     This function is responsible
#     for verifying the specs of the VM before creating it.
#     """
#     try:
#         response, status_code = provider_get_requests.providers_query(request)
        
#         if status_code != 200:
#             return jsonify({"error": "Failed to verify the specs"}), 500

#         can_create = response.get_json().get('can_create')

#         if can_create:
#             return jsonify({"message": "VM can be created"}), 200
#         else:
#             return jsonify({"error": "VM can't be created"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

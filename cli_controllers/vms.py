from flask import jsonify,request

# internal imports
from provider_controllers import vm_crud

def vmStatus(subpath):
    """
    This function is responsible for returning the telemetries of the VMs.
    """
    if(subpath=="all"):
       return vmStatus_vms()
    elif(subpath=="a"):
       return vmStatus_vms_a()
    elif(subpath=="start"):
        return vmStatus_vm_start(request)
    elif(subpath=="stop"):
        return vmStatus_vm_stop(request)
    elif(subpath=="rm"):
        return vmStatus_vm_rm(request)
    elif(subpath=="rm-f"):
        return vmStatus_vm_rm_force(request)
    

def vmStatus_vms():
    """
    This function is responsible
    for returning the lists of all the active vms along with their wireguard connection status.
    """
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

def vmStatus_vms_a():
    """
    This function is responsible
    for returning the lists of all the inactive vms.
    """
    # here the inactive vms are to be fetched from 3 views- inactive_vms, active_vms and heartbeat
    # if the vm is active and it's heartbeat is not received then it's status is changed to inactive
    return jsonify(
        {
            "inactive_vms": [
                {
                    "vm_id": "vm-1",
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

def vmStatus_vm_start(request):
    """
    This function is responsible for starting an inactive vm with the vm_id/vm_name.
    """
    vm_id=request.args.get('vm_id')
    # fetch vm_name from db using vm_id & provider_id
    vm_name="Ubuntu"
    provider_id="123"
    response= vm_crud.helper_activate_vm(provider_id, vm_name)

    if response[1]==200:
        return jsonify({"message": f"VM {vm_id} is successfully started"}), 200
    else:
        return jsonify({"error": "Failed to start VM"}), 500

def vmStatus_vm_stop(request):
    """
    This function is responsible for stopping an active vm with the vm_id/vm_name.
    """
    vm_id=request.args.get('vm_id')
    # fetch vm_name from db using vm_id & provider_id
    vm_name="Ubuntu"
    provider_id="123"
    response= vm_crud.helper_deactivate_vm(provider_id, vm_name)

    if response[1]==200:
        return jsonify({"message": f"VM {vm_id} is successfully stopped"}), 200
    else:
        return jsonify({"error": "Failed to stop the VM"}), 500

def vmStatus_vm_rm(request):
    """
    This function is responsible
    for removing an inactive vm with the vm_id/vm_name.
    """
    vm_id=request.args.get('vm_id')
    # fetch vm_name from db using vm_id & provider_id
    # check if the vm is inactive by checking the inactive table and check if it's active but heartbeat is not received

    is_vm_active=False
    if is_vm_active:
        return jsonify({"error": "VM is still active.To forcefully inactive it try with command 'rm -f' or else first deactivate the vm"}), 500
    else:
        vm_name="Ubuntu"
        provider_id="123"
        response= vm_crud.helper_delete_vm(provider_id, vm_name)

        if response[1]==200:
            return jsonify({"message": f"Inactive-VM {vm_id}  is successfully deleted"}), 200
        else:
            return jsonify({"error": "Failed to delete the VM"}), 500

def vmStatus_vm_rm_force(request):
    """
    This function is responsible for forcefully removing an active vm with the vm_id/vm_name.
    """
    vm_id=request.args.get('vm_id')
    # fetch vm_name from db using vm_id & provider_id
    vm_name="Ubuntu"
    provider_id="123"
    response= vm_crud.helper_delete_vm(provider_id, vm_name)

    if response[1]==200:
        return jsonify({"message": "VM is successfully force deleted"}), 200
    else:
        return jsonify({"error": "Failed to force delete VM"}), 500
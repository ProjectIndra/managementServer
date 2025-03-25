from flask import jsonify,request

def providers(subpath):
    """
    This function is responsible for returning the telemetries of providers.
    """
    if(subpath=="lists"):
       return providers_lists(request)
    elif(subpath=="details"):
         return providers_details(request)
    elif(subpath=="query"):
        return providers_query(request)
    
def providers_lists(request):
    """
    This function is responsible
    for returning the lists of all the active providers
    """
    # return jsonify({"error": "Invalid "}), 400
    return jsonify(
        {
            "all_providers": [
                {
                    # "user_id": "user-1",
                    "provider_id": "provider-1",
                    "provider_name": "provider-1",
                    "provider_max_ram": "8GB",
                    "provider_max_vcpu": "4",
                    "provider_max_storage": "10GB",
                    "provider_rating": 3.5,
                    "provider_status": "active",
                },
                {
                    # "user_id": "user-2",
                    "provider_id": "provider-2",
                    "provider_name": "provider-2",
                    "provider_max_ram": "16GB",
                    "provider_max_vcpu": "8",
                    "provider_max_storage": "20GB",
                    "provider_rating": 3.5,
                    "provider_status": "active",
                }
            ]
        }
    ), 200

def providers_details(request):
    """
    This function is responsible
    for returning the details i.e. vcpu and ram of a given provider.
    """
    provider_id=request.args.get('provider_id')
    return jsonify(
        {
                    "provider_id": "provider-1",
                    "provider_name": "provider-1",
                    "provider_ram": "8GB",
                    "provider_cpu": "4",
                    "provider_status": True
        }
    ), 200

def providers_query(request):
    """
    This function returns whether the user can create a vm or not with the given requriements for a provider.
    params:- vcpu,ram,storage,provider_id
    """
    vcpu=request.args.get('vcpu')
    ram=request.args.get('ram')
    storage=request.args.get('storage')
    provider_id=request.args.get('provider_id')
    vm_image_type=request.args.get('vm_image_type')
    return jsonify(
        {
            "can_create": False
        }
    ), 200

# def providers_createVm(request):
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
    return jsonify(
        {
            "active_providers": [
                {
                    "provider_id": "provider-1",
                    "provider_name": "provider-1",
                    "provider_ram": "8GB",
                    "provider_cpu": "4",
                    "provider_status": "active",
                },
                {
                    "provider_id": "provider-2",
                    "provider_name": "provider-2",
                    "provider_ram": "16GB",
                    "provider_cpu": "8",
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
    return jsonify(
        {
            "can_create": True
        }
    ), 200

# def providers_createVm(request):
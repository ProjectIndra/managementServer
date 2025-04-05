from flask import request, jsonify
import requests
# from datetime import datetime, timedelta
# import jwt
import os
from dbConnection import db
from models import authModels
from models.vmsModel import vm_details_collection


# SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")

def heartbeat():
    data = request.json

    print(f"dyyryrh{data}")
    token=data["token"]
    username=data["username"]
    link=data["link"]


    if not token or not username:
        return jsonify({"error": "Token and username are required"}), 401

    # Check if user exists
    user = authModels.users_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "Unauthorized: User not found"}), 401


    # need to store the session, if the gap is less than 5 sec then consider it in the previous session otherwise consider it as different session
    # also save/update the provider link ( 'https://pet-muskox-honestly.ngrok-free.app') if the session changes(or new session start)


    return jsonify({"success": "Authorized: Valid token"}), 200



def vm_telemetry(provider_id, subpath):



    try:
        
        # fetching provider url from the DB using provider_id
        provider=vm_details_collection.find_one({"provider_id":provider_id},{"_id":0,"provider_url":1})
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        provider_url=provider.get('provider_url')
        if not provider_url:
            return jsonify({"error": "Provider URL not found"}), 404
        

        full_url = f"{provider_url}/{subpath}"

        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        # also add the token to the headers
        token =provider.get('management_server_verification_token')
        if token:
            headers['authorization'] = token

        response = requests.request(
            method=request.method,
            url=full_url,
            headers=headers,
            data=request.get_data() if request.method in ["POST", "PUT", "PATCH"] else None,
            params=request.args,
            allow_redirects=False
        )

        return response.content, response.status_code, response.headers.items()

    except requests.RequestException as e:
        print(f"Proxy error: {e}")  # Debugging log
        return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500



# def request_vm(provider_id, subpath, method, data):
#     provider_url = "https://pet-muskox-honestly.ngrok-free.app"
#     full_url = f"{provider_url}/{subpath}"

#     print(f"Proxying request: {method} {full_url}")  # Debugging log
#     print(f"Request data: {data}")  # Debugging log

#     try:
#         headers = {key: value for key, value in request.headers if key.lower() != 'host'}

#         response = requests.request(
#             method=method,
#             url=full_url,
#             headers=headers,
#             json=data if method in ["POST", "PUT", "PATCH"] else None,
#             params=request.args,
#             allow_redirects=False
#         )

#         print(f"Response from provider: {response.status_code}")  # Debugging log
#         print(f"Response content: {response.text}")  # Debugging log

#         return response.content, response.status_code, response.headers.items()

#     except requests.RequestException as e:
#         print(f"Proxy error: {e}")  # Debugging log
#         return jsonify({"error": "Failed to reach provider", "details": str(e)}), 500

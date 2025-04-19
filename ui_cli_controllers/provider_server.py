import jwt
import uuid
from datetime import datetime, timedelta
from flask import request, jsonify, make_response
import os
from dotenv import load_dotenv
# from flask_bcrypt import Bcrypt
# from cryptography.fernet import Fernet
# from marshmallow import ValidationError

# internal imports

from models.providers import provider_details_collection, provider_conf_collection
from models.authModels import users_collection


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key").encode()  # Ensure it's bytes

def verify_provider_token():
    """
    This function verifies the provider verification token.
    """
    try:
        data = request.json
        provider_verification_token = data.get("provider_verification_token")
        provider_allowed_vms=data.get('max_vms')
        provider_allowed_networks=data.get('max_networks')
        provider_allowed_ram=data.get('max_ram')
        provider_allowed_vcpu=data.get('max_cpu')
        provider_allowed_storage=data.get('max_disk')
        provider_ram_capacity=data.get('ram_capacity')
        provider_vcpu_capacity=data.get('cpu_capacity')
        provider_storage_capacity=data.get('disk_capacity')
        provider_url=data.get('provider_url')

        if not provider_verification_token:
            return jsonify({"error": "Token is required"}), 400

        # Decode the JWT token
        decoded_token = jwt.decode(provider_verification_token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_token.get("user_id")
        provider_id = decoded_token.get("provider_id")
        # print(user_id,provider_id)
        if not user_id or not provider_id:
            return jsonify({"error": "user_id and provider_id are not present in token"}), 401

        # Check if the user exists in the database
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            return jsonify({"error": "Invalid User"}), 404

        # Check if the token has expired
        # expiry_time = decoded_token.get("exp")
        # if not expiry_time or datetime.utcnow() > datetime.utcfromtimestamp(expiry_time):
        #     return jsonify({"error": "Token expired"}), 401
        
        # check if the provider already exists in the database through provider_id
        provider = provider_details_collection.find_one({"provider_id": provider_id})
        management_server_verification_token = str(uuid.uuid4())

        if not provider:
            # create a new provider
            # generating a random string for provider name
            provider_name = f"provider-{str(uuid.uuid4())}"
            provider_details_collection.insert_one({
                "user_id": user_id,
                "provider_id": provider_id,
                "provider_name": provider_name,
                "provider_status": "active",
                "provider_ram_capacity": provider_ram_capacity,
                "provider_vcpu_capacity": provider_vcpu_capacity,
                "provider_storage_capacity": provider_storage_capacity,
                "provider_used_ram": 0,
                "provider_used_vcpu": 0,
                "provider_used_storage": 0,
                "provider_used_networks": 0,
                "provider_used_vms": 0,
                "provider_rating": 0,
                "provider_url": provider_url,
                "management_server_verification_token": management_server_verification_token
            })

            # create provider configuration
            provider_conf_collection.insert_one({
                "provider_id": provider_id,
                "provider_allowed_ram": provider_allowed_ram,
                "provider_allowed_vcpu": provider_allowed_vcpu,
                "provider_allowed_storage": provider_allowed_storage,
                "provider_allowed_vms": provider_allowed_vms,
                "provider_allowed_networks": provider_allowed_networks,
                "conf_created_at": datetime.now()
            })

        else:
            # update the provider details
            provider_details_collection.update_one(
                {"provider_id": provider_id},
                {
                    "$set": {
                        "provider_ram_capacity": provider_ram_capacity,
                        "provider_vcpu_capacity": provider_vcpu_capacity,
                        "provider_storage_capacity": provider_storage_capacity,
                        "provider_url": provider_url,
                        "provider_status": "active",
                        "management_server_verification_token": management_server_verification_token
                    }
                }
            )

            # update the provider configuration
            provider_conf_collection.update_one(
                {"provider_id": provider_id},
                {
                    "$set": {
                        "provider_allowed_ram": provider_allowed_ram,
                        "provider_allowed_vcpu": provider_allowed_vcpu,
                        "provider_allowed_storage": provider_allowed_storage,
                        "provider_allowed_vms": provider_allowed_vms,
                        "provider_allowed_networks": provider_allowed_networks,
                        "conf_updated_at": datetime.now()
                    }
                }
            )

        
        # # Update the token in the provider's database
        # provider_details_collection.update_one(
        #     {"provider_id": user_id},
        #     {"$set": {"management_server_verification_token": management_server_verification_token}}
        # )

        return jsonify({"message": "Provider token verified successfully","management_server_verification_token":management_server_verification_token}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_config():
    """
    This function is responsible for getting the server configuration.
    """
    try:
        data = request.json
        management_server_verification_token = data.get("management_server_verification_token")

        if not management_server_verification_token:
            return jsonify({"error": "Token is required"}), 400
        
        # check whether the token is valid or not in the provider database
        provider = provider_details_collection.find_one({"management_server_verification_token": management_server_verification_token},{"provider_id":1})

        if not provider:
            return jsonify({"error": "Invalid Token"}), 401
        provider_id = provider.get("provider_id")
        
        # fetch the provider configuration
        provider_conf = provider_conf_collection.find_one({"provider_id": provider_id})
        if not provider_conf:
            return jsonify({"error": "Provider configuration not found"}), 404
        # Extract the provider configuration
        max_ram = provider_conf.get("provider_allowed_ram")
        max_vcpu = provider_conf.get("provider_allowed_vcpu")
        max_disk = provider_conf.get("provider_allowed_storage")
        max_vms = provider_conf.get("provider_allowed_vms")
        max_networks = provider_conf.get("provider_allowed_networks")

        # Return the provider configuration
        return jsonify({
            "max_ram": max_ram,
            "max_cpu": max_vcpu,
            "max_disk": max_disk,
            "max_vms": max_vms,
            "max_networks": max_networks
        }), 200
    
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
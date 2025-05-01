from prometheus_api_client import PrometheusConnect
from flask import request
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Prometheus
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

def query_prometheus(subpath):
    """
    Query Prometheus metrics for a specific server.
    :param subpath: Metric type (e.g., vm_ram_used)
    :param server_address: The target server address (e.g., 192.168.1.10:5000)
    """
    try:
        # server_address = request.args.get("server_address")
        server_address = request.json.get("server_address", "https://pet-muskox-honestly.ngrok-free.app/metrics")
        server_address = server_address.replace("https://", "").replace("http://", "")
        if not server_address:
            return {"error": "Server address is required"}, 400
        if subpath == "vm_ram_used":
            return vm_ram_used_query(server_address)
        elif subpath == "vm_cpu_used":
            return vm_cpu_used_query(server_address)
        elif subpath == "vm_storage_used":
            return vm_storage_used_query(server_address)
        else:
            return {"error": "Invalid query type"}, 400
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query Prometheus"}, 500


def vm_ram_used_query(server_address):
    try:
        query = f'vm_ram_used{{instance="{server_address}"}}'
        query_result = prom.custom_query(query=query)
        print(f"Query result for vm_ram_used: {query_result}")
        return query_result, 200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query RAM metric"}, 500

def vm_cpu_used_query(server_address):
    try:
        query_result = prom.custom_query(
            query=f'vm_cpu_used{{instance="{server_address}"}}'
        )
        return query_result, 200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query CPU metric"}, 500


def vm_storage_used_query(server_address):
    try:
        query_result = prom.custom_query(
            query=f'vm_storage_used{{instance="{server_address}"}}'
        )
        return query_result, 200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query storage metric"}, 500

from prometheus_api_client import PrometheusConnect
from flask import Flask, request


# Connect to Prometheus
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

def query_prometheus(subpath):
    """
    This function is responsible for querying the Prometheus server.
    It handles different types of queries based on the provided parameters.
    """
    try:
        if subpath=="vm_ram_used":
            print(subpath)
            return vm_ram_used_query()
        elif subpath=="vm_cpu_used":
            return vm_cpu_used_query()
        elif subpath=="vm_storage_used":
            return vm_storage_used_query()  
        else :
            return {"error": "Invalid query type"}, 400
        
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query Prometheus"}, 500

def vm_ram_used_query():
    try:
        # Query for vm_ram_used
        query_result = prom.custom_query(query="vm_ram_used")

        # Print the result
        print(query_result)
        return query_result,200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query Prometheus"}, 500

def vm_cpu_used_query():
    try:
        # Query for vm_cpu_used
        query_result = prom.custom_query(query="vm_cpu_used")

        # Print the result
        print(query_result)
        return query_result,200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query Prometheus"}, 500

def vm_storage_used_query():
    try:
        # Query for vm_storage_used
        query_result = prom.custom_query(query="vm_storage_used")

        # Print the result
        print(query_result)
        return query_result,200
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return {"error": "Failed to query Prometheus"}, 500


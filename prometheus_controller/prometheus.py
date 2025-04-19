from prometheus_api_client import PrometheusConnect
from flask import Flask, request
import yaml
import os
from dotenv import load_dotenv


load_dotenv()
# Connect to Prometheus
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)


def update_prometheus_conf():
    """
    This function is responsible for adding a new target to the Prometheus configuration file.
    It checks if the target already exists and updates the configuration accordingly.
    """
    data= request.json
    new_target = data.get("new_target")
    if not new_target:
        return {"error": "Target/provider_url is required"}, 400
    config_path = os.getenv('PROMETHEUS_CONFIG_PATH')
    if not config_path:
        raise EnvironmentError("PROMETHEUS_CONFIG_PATH environment variable not set.")

    # Remove scheme (http:// or https://) if present
    new_target = new_target.split("://")[-1]
    print(f"New target to add: {new_target}")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    for job in config.get('scrape_configs', []):
        if job.get('job_name') == 'provider_metrics':
            static_configs = job.setdefault('static_configs', [])
            if static_configs:
                targets = static_configs[0].setdefault('targets', [])
                if new_target not in targets:
                    targets.append(new_target)
                    print(f"Added target: {new_target}")
                else:
                    print(f"Target {new_target} already exists.")
            else:
                job['static_configs'] = [{'targets': [new_target]}]
            break
    else:
        config.setdefault('scrape_configs', []).append({
            'job_name': 'provider_metrics',
            'metrics_path': '/metrics',
            'static_configs': [{'targets': [new_target]}]
        })
        print(f"Created new job and added target: {new_target}")

    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

    return {"message": "Prometheus configuration updated successfully"}, 200



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


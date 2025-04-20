from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import pymongo
import os
import requests  # Used for HTTP API requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

# MongoDB setup
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client["project-badal-db"]
collection = db["metric_dumps"]

# Metrics to track
METRICS = [
    "provider_heartbeat", "active_vms", "inactive_vms", "vm_state",
    "vm_cpu_allocated", "vm_ram_allocated", "vm_cpu_used", "vm_ram_used",
    "network_active", "network_inactive"
]

# Time window: past 2 hours
end_time = datetime.now()
start_time = end_time - timedelta(hours=2)


def get_all_targets():
    try:
        # Fetch all targets from Prometheus' /api/v1/targets endpoint
        response = requests.get("http://localhost:9090/api/v1/targets")
        if response.status_code == 200:
            targets_data = response.json()
            targets = []
            # Merge both active and dropped targets
            for target in targets_data.get("data", {}).get("activeTargets", []):
                instance = target.get("labels", {}).get("instance")
                if instance:
                    targets.append(instance)
            for target in targets_data.get("data", {}).get("droppedTargets", []):
                instance = target.get("labels", {}).get("instance")
                if instance:
                    targets.append(instance)
            return targets
        else:
            print(f"Failed to fetch targets, status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching targets: {e}")
        return []


def dump_data():
    try:
        all_changes = []

        # Get all available targets (including inactive ones)
        targets = get_all_targets()

        # For each target (instance), fetch data for the metrics
        for instance in targets:
            print(f"Fetching data for instance: {instance}")

            for metric in METRICS:
                try:
                    # Fetch data for each metric for the given target/instance
                    query = f'{metric}{{instance="{instance}"}}'  # Add filter for the instance
                    result = prom.custom_query_range(
                        query=query,
                        start_time=start_time,
                        end_time=end_time,
                        step=300
                    )
                except Exception as e:
                    print(f"Error querying {metric} for {instance}: {e}")
                    continue

                # Process the fetched data
                for series in result:
                    values = series.get("values", [])
                    labels = series.get("metric", {})
                    last_val = None

                    for ts, val in values:
                        try:
                            val = float(val)
                        except ValueError:
                            continue  # Skip if value is not a float (e.g., 'NaN')

                        if last_val is None or val != last_val:
                            entry = {
                                "metric": metric,
                                "vm": labels.get("vm"),
                                "instance": instance,
                                "timestamp": datetime.fromtimestamp(float(ts)),
                                "value": str(val)
                            }
                            all_changes.append(entry)
                            last_val = val

        # Insert data into MongoDB
        if all_changes:
            collection.insert_many(all_changes)
            print(f"{len(all_changes)} metric changes inserted.")
            return({"message": "Data dumped successfully"}), 200
        else:
            print("No changes detected in this 2-hour window.")
            return({"message": "No changes detected"}), 200

    except Exception as e:
        print(f"Error in dump_data: {e}")
        return({"error": "Failed to dump data"}), 500


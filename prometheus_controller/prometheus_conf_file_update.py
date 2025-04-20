import os
import yaml
from dotenv import load_dotenv


load_dotenv()

PROMETHEUS_CONFIG_PATH = os.getenv("PROMETHEUS_CONFIG_PATH", "prometheus.yml")


def add_prometheus_target(provider_url):
    """
    Adds a target to the Prometheus configuration file.
    If the target already exists, it returns a 208 status code.
    """
    try:
        target = provider_url.replace("https://", "").replace("http://", "")
        with open(PROMETHEUS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        for job in scrape_configs:
            if job.get("job_name") == "provider_metrics":
                existing_targets = job.get("static_configs", [{}])[0].get("targets", [])
                if target in existing_targets:
                    return False, 208  # Already exists
                existing_targets.append(target)
                job["static_configs"][0]["targets"] = existing_targets
                break
        else:
            # job_name does not exist, create it
            scrape_configs.append({
                "job_name": "provider_metrics",
                "metrics_path": "/metrics",
                "static_configs": [{"targets": [target]}]
            })

        config["scrape_configs"] = scrape_configs

        with open(PROMETHEUS_CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        return True, 200

    except Exception as e:
        return str(e), 500


def remove_prometheus_target(provider_url):
    """
    Removes a target from the Prometheus configuration file.
    If the target does not exist, it returns a 404 status code.
    """
    try:
        target = provider_url.replace("https://", "").replace("http://", "")
        with open(PROMETHEUS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        updated = False
        scrape_configs = config.get("scrape_configs", [])
        for job in scrape_configs:
            if job.get("job_name") == "provider_metrics":
                targets = job.get("static_configs", [{}])[0].get("targets", [])
                if target in targets:
                    targets.remove(target)
                    updated = True
                job["static_configs"][0]["targets"] = targets

        if updated:
            with open(PROMETHEUS_CONFIG_PATH, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        return updated

    except Exception:
        return False

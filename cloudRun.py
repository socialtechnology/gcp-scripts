import subprocess
import json
import csv
import sys
from datetime import datetime

def get_cloud_run_info(project=None):
    cmd = "gcloud run services list --format=json"
    if project:
        cmd += f" --project {project}"

    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud command: {e}")
        return []

    services = json.loads(output)

    cloud_run_info = []
    for service in services:
        service_name = service.get("metadata", {}).get("name", "N/A")
        service_url = service.get("status", {}).get("address", {}).get("url", "N/A")
        cpu_limit = service.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("resources", {}).get("limits", {}).get("cpu", "N/A")
        memory_limit = service.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("resources", {}).get("limits", {}).get("memory", "N/A")
        
        annotations = service.get("spec", {}).get("template", {}).get("metadata", {}).get("annotations", {})
        min_instances = annotations.get("autoscaling.knative.dev/minScale", "N/A")
        max_instances = annotations.get("autoscaling.knative.dev/maxScale", "N/A")
        
        startup_cpu_boost_annotation = annotations.get("run.googleapis.com/startup-cpu-boost", "false").replace('\xa0', ' ').strip()
        startup_cpu_boost = "Enabled" if startup_cpu_boost_annotation.lower() == "true" else "Disabled"
        
        last_deploy = service.get("status", {}).get("conditions", [{}])[0].get("lastTransitionTime", "N/A")
        
        last_deploy = datetime.strptime(last_deploy, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S") if last_deploy != "N/A" else "N/A"

        cloud_run_info.append({
            "Service Name": service_name,
            "Service URL": service_url,
            "CPU Limit (yaml)": cpu_limit,
            "Memory Limit (yaml)": memory_limit,
            "Min Instances": min_instances,
            "Max Instances": max_instances,
            "Startup CPU Boost": startup_cpu_boost,
            "Last Deploy": last_deploy,
        })

    return cloud_run_info

def write_to_csv(data, filename="cloud_run_info.csv"):
    keys = data[0].keys() if data else []
    with open(filename, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    project_name = sys.argv[1] if len(sys.argv) > 1 else None

    cloud_run_info = get_cloud_run_info(project=project_name)

    for info in cloud_run_info:
        print(info)

    write_to_csv(cloud_run_info)

    print("Data has been written to cloud_run_info.csv")

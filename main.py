import subprocess
import json
import csv
import sys

defaultProjectId = "yourProjectId"

def get_machine_type_info(machine_type, project, zone):
    cmd_memory = f"gcloud compute machine-types describe {machine_type} --project {project} --zone {zone} --format='value(memoryMb)'"
    cmd_cpu = f"gcloud compute machine-types describe {machine_type} --project {project} --zone {zone} --format='value(guestCpus)'"

    try:
        memory_mb = subprocess.check_output(cmd_memory, shell=True, text=True).strip()
        cpu = subprocess.check_output(cmd_cpu, shell=True, text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud command: {e}")
        print(f"Command output:\n{e.output}")
        return "N/A", "N/A"

    return memory_mb, cpu

def get_gcp_instance_info(project=None):
    cmd = "gcloud compute instances list --format=json"
    if project:
        cmd += f" --project {project}"

    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud command: {e}")
        return []

    instances = json.loads(output)

    instance_info = []
    for instance in instances:
        instance_name = instance.get("name", "N/A")
        machine_type = instance.get("machineType", "").split("/")[-1]
        os = instance.get("disks", [{}])[0].get("licenses", ["Unknown OS"])[0].split("/")[-1]
        status = instance.get("status", "N/A")

        zone = instance.get("zone", "").split("/")[-1]

        memory_mb, cpu = get_machine_type_info(machine_type, project=project, zone=zone)

        memory_gb = f"{int(memory_mb) / 1024:.2f}" if memory_mb != "N/A" else "N/A"

        internal_ip = instance.get("networkInterfaces", [{}])[0].get("networkIP", "N/A")
        external_ip = instance.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP", "N/A")

        disks_info = []
        for disk in instance.get("disks", []):
            disk_name = disk.get("deviceName", "N/A")
            disk_size_gb = disk.get("diskSizeGb", "N/A")
            disks_info.append({"Disk Name": disk_name, "Disk Size (GB)": disk_size_gb})

        instance_info.append({
            "Instance Name": instance_name,
            "Machine Type": machine_type,
            "Operating System": os,
            "Status": status,
            "CPU": cpu,
            "Memory (GB)": memory_gb,
            "Zone": zone,
            "Internal IP": internal_ip,
            "External IP": external_ip,
            "Disks": disks_info,
        })

    return instance_info

def write_to_csv(data, filename="gcp_instance_info.csv"):
    keys = data[0].keys() if data else []
    with open(filename, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    project_name = sys.argv[1] if len(sys.argv) > 1 else defaultProjectId

    gcp_instance_info = get_gcp_instance_info(project=project_name)

    write_to_csv(gcp_instance_info)

    print("Data has been written to gcp_instance_info.csv")

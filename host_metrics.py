import json, subprocess, os, time, serial
import requests


## Get the primary IP address (on the local network)
def get_ip_address():
    try:
        # Run ip route to find the default interface
        cmd = "ip route | grep default | awk '{print $5}'"
        interface = subprocess.check_output(cmd, shell=True).decode().strip()
        
        # Get the IP address for that interface
        cmd = f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1"
        ip = subprocess.check_output(cmd, shell=True).decode().strip()
        return ip
    except subprocess.SubprocessError:
        # Fallback method if the above fails
        try:
            cmd = "hostname -I | awk '{print $1}'"
            return subprocess.check_output(cmd, shell=True).decode().strip()
        except:
            return "127.0.0.1"  # Return localhost if all else fails

## Check if Docker is running
def is_docker_running():
    return subprocess.call(
        ["systemctl", "is-active", "--quiet", "docker"]
    ) == 0

## Check if Eutax server is healthy
def is_eutax_healthy():
    try:
        ## Make a GET request to the health endpoint
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        
        ## Check if response is successful and has the right status
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                return True
        return False
    except Exception as e:
        return False

## Get the uptime in days (1 decimal place)
def uptime_days():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.read().split()[0])
    return round(uptime_seconds / 86400, 1)

## Get the number of Eutax jobs
def eutax_job_count():
    try:
        response = requests.get("http://localhost:8000/api/v1/job_count", timeout=5)
        if response.status_code == 200:
            return int(response.text)
        return 0
    except Exception as e:
        return 0


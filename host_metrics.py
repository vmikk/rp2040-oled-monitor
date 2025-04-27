import json, subprocess, os, time, serial


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


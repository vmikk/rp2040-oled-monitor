import json, subprocess, os, time, serial
import requests
# import cbor2  # CBOR serialization library - not supported in CircuitPython yet


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

## Gather metrics
def gather():
    return {
        "ip":         get_ip_address(),
        "docker":     is_docker_running(),
        "uptime":     uptime_days(),
        "eutax":      is_eutax_healthy(),
        "eutax_jobs": eutax_job_count()
    }

## Send metrics to the serial port
def send(m):
    """
    Serialize metrics using a simple pipe-delimited format
    E.g., "key1:value1|key2:value2|key3:value3"
    Boolean values are represented as 'true'/'false' strings
    """
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
        # Create pipe-delimited string of key:value pairs
        parts = []
        for key, value in m.items():
            # Convert boolean values to true/false strings
            if isinstance(value, bool):
                value = "true" if value else "false"
            parts.append(f"{key}:{value}")
        
        data = "|".join(parts) + "\n"    # Add newline as message terminator
        ser.write(data.encode("ascii"))

# def send_cbor(m):
#     """
#     Serialize metrics using CBOR (Concise Binary Object Representation) and send over serial.
#     CBOR advantages:
#     - Compact binary format (smaller payload than JSON)
#     - Efficient encoding/decoding for resource-constrained devices
#     - Self-describing format that preserves data types
#     - Specifically designed for IoT and machine-to-machine communication
#     """
#     with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
#         # Convert Python dictionary to CBOR binary data
#         cbor_data = cbor2.dumps(m)
#         ser.write(cbor_data)


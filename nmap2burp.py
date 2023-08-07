import os
import subprocess
import requests
import time
import xml.etree.ElementTree as ET

# Replace with the path to your Burp Suite installation
BURP_SUITE_PATH = "/path/to/burp_suite.jar"

# Replace with the IP address or hostname of the target host
TARGET_HOST = "target_host"

# Function to run Nmap scan and parse the XML output
def run_nmap_scan():
    nmap_output = "nmap_output.xml"
    nmap_cmd = ["nmap", "-oX", nmap_output, TARGET_HOST]
    subprocess.run(nmap_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    open_ports = []
    try:
        tree = ET.parse(nmap_output)
        root = tree.getroot()
        for host in root.findall(".//host"):
            for port in host.findall(".//port"):
                state = port.find("state")
                if state is not None and state.get("state") == "open":
                    portid = port.get("portid")
                    open_ports.append(portid)
    except ET.ParseError as e:
        print(f"Error parsing Nmap output: {str(e)}")

    os.remove(nmap_output)
    return open_ports

# Function to start Burp Suite in headless mode
def start_burp():
    burp_cmd = ["java", "-jar", BURP_SUITE_PATH, "--unpause-spider-and-scanner", "--project-file", "project.burp", "--config-file", "config.json"]
    subprocess.Popen(burp_cmd)

# Function to check if the scan is complete
def is_scan_complete():
    burp_api_url = "http://127.0.0.1:1337/v0.1/status"
    response = requests.get(burp_api_url)
    if response.status_code == 200:
        scan_status = response.json()["scanStatus"]
        return scan_status.lower() == "idle"
    return False

# Function to save the Burp Suite project file
def save_burp_project():
    burp_api_url = "http://127.0.0.1:1337/v0.1/configuration/save"
    headers = {"Content-Type": "application/json"}
    data = {
        "filename": "project.burp"
    }
    response = requests.post(burp_api_url, headers=headers, json=data)
    if response.status_code == 200:
        print("Burp Suite project saved.")
    else:
        print("Failed to save Burp Suite project.")

# Function to initiate the Burp Suite scan for a specific target URL
def start_burp_scan(target_url):
    burp_api_url = "http://127.0.0.1:1337/v0.1/scan"
    headers = {"Content-Type": "application/json"}
    data = {
        "url": target_url,
        "checks": ["active", "passive"],
        "scope": ["baseUrl=" + target_url],
        "scanConfigurations": ["Default"]
    }
    response = requests.post(burp_api_url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Burp Suite scan started for {target_url}")
    else:
        print(f"Failed to start Burp Suite scan for {target_url}")

# Main script
if __name__ == "__main__":
    try:
        # Start Burp Suite in headless mode
        start_burp()

        # Wait for Burp Suite to initialize
        time.sleep(10)

        # Get open ports from Nmap scan
        open_ports = run_nmap_scan()
        if not open_ports:
            print("No open ports found.")
            exit()

        # Perform the Burp Suite scan for each target URL
        for port in open_ports:
            target_url = f"http://{TARGET_HOST}:{port}"
            start_burp_scan(target_url)

        # Monitor the progress of the scan
        while not is_scan_complete():
            time.sleep(10)

        # Save the Burp Suite project file at the end
        save_burp_project()

    except KeyboardInterrupt:
        print("Script interrupted.")

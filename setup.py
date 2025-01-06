import os
import subprocess
import zipfile
import urllib.request
from pathlib import Path

def create_local_bin_directory():
    subprocess.check_call(["sudo", "apt", "update"])

    # Get the current user's home directory
    home_dir = str(Path.home())

    # Define the path for ~/.local/bin
    local_bin_dir = os.path.join(home_dir, '.local', 'bin')

    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(local_bin_dir):
        os.makedirs(local_bin_dir)
        print(f"Created directory: {local_bin_dir}")
    else:
        print(f"Directory already exists: {local_bin_dir}")

def install_requirements():
    # Define the pip packages to install
    packages = ["wfuzz", "ansi2html"]
    
    # Use subprocess to run the pip install command
    try:
        subprocess.check_call([ "python3", "-m", "pip", "install", *packages, "--break-system-packages"])
        print("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")

def install_feroxbuster():
    # Define the URL for the install-nix.sh script
    url = "https://raw.githubusercontent.com/epi052/feroxbuster/main/install-nix.sh"
    
    # Define the installation directory
    install_dir = os.path.join(str(os.path.expanduser('~')), '.local', 'bin')
    
    # Run the curl command and pipe to bash using subprocess.run
    try:
        command = f"curl -sL {url} | bash -s {install_dir}"
        subprocess.run(command, shell=True, check=True)
        print(f"Feroxbuster installed to {install_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Feroxbuster: {e}")

def install_eyewitness():
    # Define the command to install Eyewitness
    command = ["sudo", "apt", "install", "-y", "eyewitness"]

    try:
        # Run the command to install Eyewitness
        subprocess.check_call(command)
        print("Eyewitness installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Eyewitness: {e}")

def install_ffuf():
    # Define the command to install ffuf
    command = ["sudo", "apt", "install", "-y", "ffuf"]

    try:
        # Run the command to install ffuf
        subprocess.check_call(command)
        print("ffuf installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffuf: {e}")

def install_whatweb():
    try:
        print("Installing WhatWeb...")
        subprocess.check_call(["sudo", "apt", "install", "-y", "whatweb"])
        print("WhatWeb installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing WhatWeb: {e}")

def install_aquatone():
    # URL for the Aquatone release
    aquatone_url = "https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip"
    download_path = "/tmp/aquatone_linux_amd64_1.7.0.zip"
    extract_dir = "/tmp/aquatone"
    
    # Destination path for the binary
    bin_dir = os.path.expanduser("~/.local/bin")
    aquatone_bin = os.path.join(bin_dir, "aquatone")
    
    # Create bin_dir if it doesn't exist
    os.makedirs(bin_dir, exist_ok=True)
    
    try:
        # Download the zip file
        print(f"Downloading Aquatone from {aquatone_url}...")
        urllib.request.urlretrieve(aquatone_url, download_path)
        
        # Extract the zip file
        print(f"Extracting to {extract_dir}...")
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find and move the binary
        extracted_binary = os.path.join(extract_dir, "aquatone")
        if os.path.exists(extracted_binary):
            subprocess.check_call(["cp", extracted_binary, aquatone_bin])
            subprocess.check_call(["chmod", "+x", aquatone_bin])
            print(f"Aquatone installed successfully to {aquatone_bin}")
        else:
            print("Error: Aquatone binary not found after extraction.")
    except Exception as e:
        print(f"Error setting up Aquatone: {e}")
    finally:
        # Clean up the downloaded zip file
        if os.path.exists(download_path):
            os.remove(download_path)
        if os.path.exists(extract_dir):
            subprocess.check_call(["rm", "-rf", extract_dir])

def setup_seclists():
    # Define the paths to check
    seclists_path = "/usr/share/seclists"
    secLists_path = "/usr/share/SecLists"
    temp_clone_path = "/tmp/SecLists"  # Temporary location for cloning

    # Check if /usr/share/seclists exists
    if os.path.exists(seclists_path):
        print(f"{seclists_path} already exists. No action needed.")
    elif os.path.exists(secLists_path):
        # If /usr/share/SecLists exists, copy it to /usr/share/seclists
        print(f"{secLists_path} exists. Moving to {seclists_path}.")
        try:
            subprocess.check_call(["sudo", "cp", "-r", secLists_path, seclists_path])
            print("SecLists copied successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error copying SecLists: {e}")
    else:
        # If neither exists, clone the repository into a temporary location
        print("SecLists not found. Cloning the repository.")
        try:
            subprocess.check_call(["sudo", "git", "clone", "-q", "https://github.com/danielmiessler/SecLists.git", temp_clone_path])
            subprocess.check_call(["sudo", "mv", temp_clone_path, seclists_path])  # Move to the correct location
            print("SecLists cloned and moved successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning or moving SecLists: {e}")

def main():
    # Create ~/.local/bin directory if it doesn't exist
    create_local_bin_directory()
    install_requirements()
    install_whatweb()
    install_feroxbuster()
    install_eyewitness()
    install_aquatone()
    setup_seclists()

if __name__ == "__main__":
    main()

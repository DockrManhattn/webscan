import os
import subprocess
from pathlib import Path

def create_local_bin_directory():
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
    packages = ["whatweb", "wfuzz", "ansi2html"]
    
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
    
    # Run the curl command and pipe to bash
    try:
        subprocess.check_call(["curl", "-sL", url, "|", "bash", "-s", install_dir])
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

def setup_seclists():
    # Define the paths to check
    seclists_path = "/usr/share/seclists"
    secLists_path = "/usr/share/SecLists"

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
        # If neither exists, clone the repository
        print("SecLists not found. Cloning the repository.")
        try:
            subprocess.check_call(["sudo", "git", "clone", "-q", "https://github.com/danielmiessler/SecLists.git", "/usr/share"])
            subprocess.check_call(["sudo", "mv", "/usr/share/SecLists", seclists_path])
            print("SecLists cloned and moved successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning or moving SecLists: {e}")



def main():
    # Create ~/.local/bin directory if it doesn't exist
    create_local_bin_directory()
    install_requirements()
    install_feroxbuster()
    install_eyewitness()
    setup_seclists()



if __name__ == "__main__":
    main()

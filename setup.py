import os
import subprocess
import zipfile
import shutil
import urllib.request
from pathlib import Path

def get_current_user_and_shell():
    """Get the current user's home directory and shell."""
    home = Path.home()  # Home directory
    user_name = home.parts[-1]  # Username is the last part of the home path
    shell = os.getenv("SHELL", "/bin/sh")  # Default to /bin/sh if $SHELL is not set
    
    return user_name, shell

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

def copy_webscan_script():
    """Copy webscan.py to the ~/.local/bin directory and make it executable."""
    # Get the current user's home directory
    home_dir = Path.home()
    
    # Define the source and destination paths
    local_bin_dir = home_dir / '.local' / 'bin'
    repo_dir = Path(__file__).parent  # Assumes setup.py is in the same directory as webscan.py
    source_file = repo_dir / 'webscan.py'
    destination_file = local_bin_dir / 'webscan.py'
    
    # Check if source file exists before copying
    if not source_file.exists():
        print(f"Error: {source_file} not found.")
        return
    
    # Copy the file and set permissions
    try:
        shutil.copy2(source_file, destination_file)
        destination_file.chmod(0o755)
        print(f"Copied {source_file} to {destination_file} and made it executable.")
    except Exception as e:
        print(f"Error copying webscan.py: {e}")

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

def install_additional_tools():
    # Define the list of additional tools to install
    tools = [
        "curl", "dnsrecon", "gobuster", "impacket-scripts", "nbtscan", "nikto", 
        "onesixtyone", "oscanner", "redis-tools", "smbclient", "smbmap", "snmp", 
        "sslscan", "sipvicious", "tnscmd10g", "whatweb"
    ]
    
    try:
        # Use subprocess to install the tools via apt
        subprocess.check_call(["sudo", "apt", "install", "-y"] + tools)
        print("Additional tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing additional tools: {e}")

def add_webscan_alias():
    """Add an alias for webscan to the shell configuration file."""
    home_dir = Path.home()
    user_shell = os.environ.get('SHELL', '')

    alias_command = f"alias webscan='python3 {home_dir}/.local/bin/webscan.py'"

    if 'zsh' in user_shell:
        rc_file = home_dir / '.zshrc'
        shell_name = 'zsh'
    elif 'bash' in user_shell:
        rc_file = home_dir / '.bashrc'
        shell_name = 'bash'
    else:
        print(f"Unsupported shell: {user_shell}. No alias added.")
        return

    try:
        with open(rc_file, 'a') as file:
            file.write(f"\n# Added by setup.py\n{alias_command}\n")
        print(f"\033[92mAlias for webscan added to {rc_file}.")
        print(f"Run 'source ~/{rc_file.name}' to apply the changes.\033[0m")
    except Exception as e:
        print(f"Error adding alias to {rc_file}: {e}")

def unzip_wordlists():
    repo_dir = Path(__file__).parent
    zip_file = repo_dir / 'wordlists.zip'
    
    local_bin_dir = Path.home() / '.local' / 'bin'
    
    if not zip_file.exists():
        print(f"Error: {zip_file} not found.")
        return
    
    if not local_bin_dir.exists():
        os.makedirs(local_bin_dir)
        print(f"Created directory: {local_bin_dir}")
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(local_bin_dir)
            print(f"Unzipped {zip_file} to {local_bin_dir}.")
    except Exception as e:
        print(f"Error unzipping {zip_file}: {e}")


def main():
    create_local_bin_directory()
    install_requirements()
    install_whatweb()
    install_feroxbuster()
    install_eyewitness()
    install_aquatone()
    install_additional_tools()
    unzip_wordlists()
    copy_webscan_script()
    add_webscan_alias()

if __name__ == "__main__":
    main()

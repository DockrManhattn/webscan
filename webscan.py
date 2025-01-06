import argparse
import os
import socket
import subprocess
import shutil
import re
from glob import glob
from datetime import datetime
from getpass import getuser
import time

# Base directory for obsidian vault
BASE_NOTEBOOK_PATH="/home/kali/notes/Boxes"

# Define ANSI color codes
YELLOW = "\033[33m"
DARK_WHITE = "\033[2;37m"
BLUE = "\033[34m"
RESET = "\033[0m"

# Define the banner as a function
def print_banner_message(message):
    """Prints a message prefixed with the banner and formatted."""
    BANNER = f"{YELLOW}{{🌀🌵[+]🌵🌀}}{RESET}"
    print(f"{BANNER} {DARK_WHITE}{message}{RESET}")

def print_error_message(message):
    """Prints an error message prefixed with an error banner and formatted."""
    ERROR_BANNER = f"{YELLOW}{{💥💀🔥[+]🔥💀💥}}{RESET}"
    print(f"{ERROR_BANNER} {DARK_WHITE}{message}{RESET}")

def check_and_create_directory(path):
    """Check if the directory exists, if not, create it."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory {path} created.")
    else:
        return

def is_ip_address(value):
    """Check if the provided value is a valid IP address."""
    try:
        socket.inet_aton(value)
        return True
    except socket.error:
        return False

def parse_arguments():
    """Parse command-line arguments and process target details."""
    parser = argparse.ArgumentParser(description="Parse a URL or IP address.")
    parser.add_argument("target", help="The URL or IP address to analyze.")
    args = parser.parse_args()

    # Process the target input
    target_input = args.target.rstrip("/")
    target, port, webpath = get_target_and_port_and_path(target_input)
    
    args.target = target
    args.port = port
    args.webpath = webpath
    args.domain = not is_ip_address(target)

    if target_input.startswith("https://"):
        args.full_url = f"https://{target}{webpath}" if port == 443 else f"https://{target}:{port}{webpath}"
    else:
        args.full_url = f"http://{target}{webpath}" if port == 80 else f"http://{target}:{port}{webpath}"

    args.full_url = args.full_url.rstrip("/")

    return args
    
def get_target_and_port_and_path(target):
    """Extract target hostname, port, and web path, setting default ports if not specified."""
    # Initialize web path as an empty string
    webpath = ""

    # Check if the target starts with http:// or https://
    if target.startswith("http://"):
        default_port = 80
        target = target[7:]  # Remove 'http://'
    elif target.startswith("https://"):
        default_port = 443
        target = target[8:]  # Remove 'https://'
    else:
        default_port = 80

    if '/' in target:
        parts = target.split("/", 1)
        target = parts[0]
        webpath = "/" + parts[1]  # Preserve everything after the first slash
    else:
        webpath = "/"  # Default path if none provided

    # Split hostname and port
    if ':' in target:
        target, port = target.split(":", 1)
        port = int(port) if port.isdigit() else default_port
    else:
        port = default_port

    return target, port, webpath

def create_notebook_directory():
    """Create a directory in BASE_NOTEBOOK_PATH based on the relative path to the home directory."""
    # Get the user's home directory
    home_dir = os.path.expanduser("~")
    current_dir = os.getcwd()

    # Calculate the relative path from the home directory
    relative_path = os.path.relpath(current_dir, home_dir)

    # Build the full path to the target notebook directory
    notebook_dir = os.path.join(BASE_NOTEBOOK_PATH, relative_path)

    # Create the directory if it doesn't exist
    os.makedirs(notebook_dir, exist_ok=True)
    return notebook_dir

def run_command(command):
    """Runs a given command and handles its output."""
    try:
        # Open a subprocess to run the command
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        # Capture the output and error streams
        stdout, stderr = process.communicate()

        # Check if the command was successful
        if process.returncode == 0:
            return stdout.decode()
        else:
            return stderr.decode()

    except Exception as e:
        return str(e)

def convert_md_to_html(md_file, notebook_dir):
    """Converts a markdown file to HTML using ansi2html and saves it in the notebook directory."""
    try:
        # Ensure the input .md file exists
        if not os.path.exists(md_file):
            raise FileNotFoundError(f"The file {md_file} does not exist.")

        # Define the output HTML file path
        html_file = os.path.join(notebook_dir, os.path.basename(md_file).replace('.md', '.html'))

        # Use subprocess to run ansi2html with a pipe (similar to `cat` in bash)
        with open(md_file, 'r') as md_input:
            with open(html_file, 'w') as html_output:
                subprocess.run(['ansi2html'], stdin=md_input, stdout=html_output, check=True)

        return html_file  # Return the path of the newly created HTML file
    except Exception as e:
        return f"Error converting file {md_file} to HTML: {str(e)}"

def run_nmap_scan(target, port, notebook_dir):
    """Defines the nmap scan command, changes the ownership of the output file, and converts the file to HTML."""
    # Define the Nmap command
    output_filename = f'020-webscan-{target}-{port}-nmap-http.md'
    nmap_command = [
        'sudo', 'nmap', '-sCV',
        '-script', 'http-webdav-scan.nse,http-userdir-enum.nse,http-shellshock.nse,http-robots.txt.nse,http-enum.nse,http-brute.nse',
        '-oN', output_filename,
        '-p', str(port), target
    ]
    command_str = " ".join(nmap_command)
    print_banner_message(f"Running Nmap: {RESET}{command_str}")


    # Run the Nmap command
    process = subprocess.Popen(nmap_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Change ownership of the nmap output file to current_user
    if process.returncode == 0:
        current_user = getuser()
        chown_command = ['sudo', 'chown', f'{current_user}:{current_user}', output_filename]
        subprocess.run(chown_command)

        # Call the function to convert the .md file to .html
        html_file = convert_md_to_html(output_filename, notebook_dir)

        # Return the Nmap command output (stdout) and the HTML file path
        return stdout.decode(), html_file
    else:
        return stderr.decode(), None

def run_whatweb_scan(target, port, notebook_dir):
    """Runs WhatWeb command on a target URL, saves the output to a markdown file in the current directory,
       converts it to HTML, and saves the HTML in the notebook directory."""
    
    # Define the output filenames
    output_md_filename = f'021-webscan-{target}-{port}-whatweb-output.md'
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)  # Save .md in the current working directory
    output_html_filename = f'021-webscan-{target}-{port}-whatweb-output.html'
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)  # HTML in notebook_dir
    
    # Construct the URL with or without port based on its value
    url = f"http://{target}" if port == 80 else f"http://{target}:{port}"
    
    # WhatWeb command with tee to save markdown output, suppressing console output
    whatweb_command = f"whatweb -v -a 3 {url} > {output_md_filepath}"
    
    # Display a shortened version of the command
    shortened_command_display = f"whatweb -v -a 3 {url} > {output_md_filename}"
    print_banner_message(f"Running WhatWeb: {RESET}{shortened_command_display}")
    
    try:
        # Execute WhatWeb command and save output to .md file
        subprocess.run(whatweb_command, shell=True, check=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert markdown file to HTML with ansi2html
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            ansi2html_command = ['ansi2html']
            process = subprocess.Popen(ansi2html_command, stdin=md_file, stdout=html_file)
            process.communicate()  # Wait for conversion to complete

        # Return paths for further processing if needed
        return output_md_filepath, output_html_filepath

    except subprocess.CalledProcessError as e:
        print_error_message(f"Error running WhatWeb scan or converting to HTML: {str(e)}")
        return None

def run_wget(url):
    """Run the wget command with the specified options."""
    # Build the wget command as a list of arguments
    wget_command = [
        "wget", "-r", "--level=0", "-E", "--ignore-length", "-x", "-k", "-p", 
        "--no-check-certificate", "-erobots=off", "-np", "-N", url
    ]
    print_banner_message(f"Running Wget: {RESET}{' '.join(wget_command)}")
    
    try:
        # Run the command using subprocess.run() and capture output
        result = subprocess.run(wget_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
    except subprocess.CalledProcessError as e:
        # Print error message if wget command fails
        print(f"Error: {e.stderr}")

def copy_site_to_notebook(target_dir, notebook_dir):
    """Copy the target directory into the notebook directory."""
    try:
        # Ensure the target directory exists
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            # Create a destination path in the notebook directory
            destination_dir = os.path.join(notebook_dir, os.path.basename(target_dir))
            
            # Check if the destination already exists and remove it if necessary
            if os.path.exists(destination_dir):
                shutil.rmtree(destination_dir)
            
            # Copy the entire target directory to the notebook directory
            shutil.copytree(target_dir, destination_dir)
        else:
            print(f"Error: The target directory {target_dir} does not exist.")
    except Exception as e:
        print(f"Error occurred while copying: {e}")

def get_target_directory(url):
    """Extracts the target directory from the full URL."""
    target = re.sub(r'^https?://', '', url)  # Remove http:// or https://
    target = target.split('/')[0]  # Only the domain or IP (with port, if present)
    return target

def extract_hostname(url):
    """Extract the hostname (domain or IP) from a full URL."""
    # Remove the protocol (http:// or https://) if present
    hostname = re.sub(r'^https?://', '', url)
    # Split by '/' and take the first part (to remove any path)
    hostname = hostname.split('/')[0]
    # Remove port if present (e.g., ':80')
    hostname = hostname.split(':')[0]
    return hostname

def run_ls_and_tee(target_dir, target, port, notebook_dir):
    """Run ls -lahR on the target directory, pipe the output to a markdown file, and convert to HTML."""
    
    # Format the output filename based on target and port
    md_output_filename = f"022-webscan-{target}-{port}-wget-directory-output.md"
    
    # Build the ls command with tee to save the output to a markdown file and also print to the terminal
    ls_command = f"ls -lahR {target_dir} | tee {md_output_filename}"
    
    try:
        # Run the ls command using subprocess
        result = subprocess.run(ls_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the markdown file is created successfully
        if os.path.exists(md_output_filename):            
            # Convert the markdown file to HTML using convert_md_to_html
            html_file = convert_md_to_html(md_output_filename, notebook_dir)
        else:
            print(f"Error: Markdown file {md_output_filename} was not created.")
    
    except subprocess.CalledProcessError as e:
        # Print error message if the ls command fails
        print(f"Error: {e.stderr}")

def run_feroxbuster(target, url, port, notebook_dir):
    """Run feroxbuster with specific options, save output to a markdown file, convert it to HTML, and extract sanitized URLs."""
    
    # Get just the domain or IP for the filename
    hostname = extract_hostname(url)
    
    # Format the output markdown filename based on hostname and port
    md_output_filename = f"023-webscan-{hostname}-{port}-ferox_basic_files.md"
    url_output_filename = f"webscan-urls-{target}-{port}.md"
    
    # Define the feroxbuster command with all specified options
    feroxbuster_command = [
        "feroxbuster",
        "-u", url,                 # Target URL
        "-k",                      # Ignore SSL certificate errors
        "--depth", "2",            # Set recursion depth to 2
        "--wordlist", "/usr/share/wordlists/dirb/common.txt",  # Path to the wordlist
        "-s", "200", "302",        # Filter status codes 200 and 302
        "--threads", "150",        # Use 150 threads
        "--extract-links",         # Extract links from responses
        "-E",                      # Automatically discover extensions and add them to
        "-B",                      # Automatically request likely backup extensions for "found"
        "-g",                      # Automatically discover important words from within responses
        "-x", "php,html", # Extensions to look for
        "-o", md_output_filename   # Output file for the results
    ]

    try:
        # Run the feroxbuster command
        print_banner_message(f"Running Feroxbuster: {RESET}{' '.join(feroxbuster_command)}")
        result = subprocess.run(feroxbuster_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Trim the markdown file to include only lines with "http://" or "https://"
        with open(md_output_filename, 'r') as md_file:
            filtered_lines = [line for line in md_file if "http://" in line or "https://" in line]

        # Overwrite the markdown file with the filtered content
        with open(md_output_filename, 'w') as md_file:
            md_file.writelines(filtered_lines)
        
        # Convert markdown to HTML
        html_output = convert_md_to_html(md_output_filename, notebook_dir)
        
        # Extract and sanitize URLs from the markdown output
        with open(md_output_filename, 'r') as md_file, open(url_output_filename, 'w') as url_file:
            urls = set()
            for line in md_file:
                for match in re.findall(r'http://[^\s]+', line):
                    sanitized_url = match.rstrip('",')
                    urls.add(sanitized_url)
            
            # Write unique, sanitized URLs to the new markdown file
            for url in sorted(urls):
                url_file.write(url + '\n')
                
    except subprocess.CalledProcessError as e:
        print(f"Error running feroxbuster: {e.stderr}")
    except Exception as e:
        print(f"Error during processing: {e}")

def run_ffuf(url, target, port, notebook_dir):
    """Run ffuf with specified options, save output to a markdown file, extract URLs, and append them to the webscan-urls file."""
    
    # Define the output filename based on target and port
    output_filename = f"024-webscan-{target}-{port}-ffuf_wordlist.md"
    url_output_filename = f"webscan-urls-{target}-{port}.md"  # Output file for sanitized URLs
    url = url.rstrip("/")

    # Define the ffuf command with the specified options
    ffuf_command = [
        "ffuf",
        "-u", f"{url}/FUZZ",                # Target URL with FUZZ placeholder
        "-w", "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt",  # Path to the wordlist
        "-ac",                              # Auto-calibrate filtering
        "-v",                               # Verbose output
        "-t", "150"                         # Set thread count to 150
    ]
    
    try:
        # Run the ffuf command and save output to the file
        with open(output_filename, 'w') as output_file:
            print_banner_message(f"Running Ffuf: {RESET}{' '.join(ffuf_command)}")
            subprocess.run(ffuf_command, check=True, stdout=output_file, stderr=subprocess.PIPE, text=True)
        
        # Convert the markdown file to HTML
        html_output = convert_md_to_html(output_filename, notebook_dir)

        # Extract and sanitize URLs from the markdown output
        with open(output_filename, 'r') as md_file, open(url_output_filename, 'w') as url_file:
            urls = set()
            for line in md_file:
                # Find URLs using a regex and sanitize them
                for match in re.findall(r'http://[^\s]+', line):
                    sanitized_url = match.rstrip('",')
                    urls.add(sanitized_url)
            
            # Write unique, sanitized URLs to the new markdown file
            for url in sorted(urls):
                url_file.write(url + '\n')
                
    except subprocess.CalledProcessError as e:
        # Handle errors from subprocess (non-zero exit codes)
        print(f"Error occurred while running ffuf: {e}")
        print(f"Error details: {e.stderr}")
    
    except Exception as e:
        # Handle any other exceptions
        print(f"An unexpected error occurred: {e}")

def run_gobuster(full_url, target, port, notebook_dir):
    """Run Gobuster and save the output to a file, then extract URLs."""
    # Use `full_url` in the Gobuster command
    gobuster_command = [
        "gobuster", "dir",
        "-w", "/usr/share/seclists/Discovery/Web-Content/big.txt",
        "-x", "php,txt,html,jpg",
        "-t", "150",
        "-q", "-n", "-e",
        "-u", full_url,  # Correctly reference `full_url` here
        "--no-error"
    ]

    print_banner_message(f"Running Gobuster: {RESET}{' '.join(gobuster_command)}")

    output_file = f"025-webscan-{target}-{port}-gobuster_wc_big.md"
    url_output_filename = f"webscan-urls-{target}-{port}.md"

    # Run Gobuster and save output to file
    with open(output_file, "w") as outfile:
        subprocess.run(gobuster_command, stdout=outfile, stderr=subprocess.PIPE, check=True)

    # Extract URLs from the Gobuster output file and save to the new file
    with open(output_file, 'r') as infile:
        lines = infile.readlines()

    # Extract URLs by selecting lines before the '[Size' text
    urls = [line.split()[0] for line in lines if 'http' in line]

    # Open the URL output file in append mode to add URLs without overwriting existing content
    with open(url_output_filename, 'a') as url_file:
        for url in urls:
            url_file.write(f"{url}\n")

    # Ensure all URLs in the file are unique
    with open(url_output_filename, 'r') as url_file:
        lines = url_file.readlines()

    # Remove duplicates by converting to a set, then back to a list to sort
    unique_urls = sorted(set(line.strip() for line in lines))

    # Write the unique URLs back to the file
    with open(url_output_filename, 'w') as url_file:
        for url in unique_urls:
            url_file.write(f"{url}\n")

    # Convert the markdown file to HTML
    html_output = convert_md_to_html(output_file, notebook_dir)
    return html_output

def convert_webscan_urls_to_html(target, port, notebook_dir):
    url_output_filename = f"webscan-urls-{target}-{port}.md"
    
    # Check if the file exists
    if not os.path.isfile(url_output_filename):
        print(f"Error: The file {url_output_filename} does not exist.")
        return None

    # Open the file and ensure the lines are unique
    with open(url_output_filename, 'r') as file:
        lines = file.readlines()

    # Remove duplicate lines by converting to a set and then back to a list
    unique_lines = list(set(lines))

    # Write the unique lines back to the file or to a new file
    with open(url_output_filename, 'w') as file:
        file.writelines(unique_lines)

    # Proceed with HTML conversion
    output_html_file = os.path.join(notebook_dir, f"webscan-urls-{target}-{port}.html")
    ansi2html_command = f"ansi2html < {url_output_filename} > {output_html_file}"
    subprocess.run(ansi2html_command, shell=True, check=True)

    return output_html_file

def fuzz_subdomains(domain, target, port, notebook_dir):
    """Fuzz for subdomains using ffuf and convert output to HTML."""
    # Output filenames
    output_md_filename = f"026-webscan-{target}-{port}-ffuf-subdomains-output.md"
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)
    output_html_filename = f"026-webscan-{target}-{port}-ffuf-subdomains-output.html"
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)
    
    # FFUF command for subdomain fuzzing
    ffuf_command = [
        "ffuf",
        "-w", "/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt:FUZZ",  # Wordlist with FUZZ placeholder
        "-u", f"http://FUZZ.{domain}",                 # Target URL with subdomain placeholder
        "-t", "150",                                   # Threads
    ]
    
    print_banner_message(f"Running Subdomain Fuzzing: {RESET}{' '.join(ffuf_command)}")

    try:
        # Execute FFUF command and save output to the markdown file
        with open(output_md_filepath, 'w') as output_file:
            subprocess.run(ffuf_command, stdout=output_file, stderr=output_file, check=True)
        
        # After FFUF completes, convert the markdown output to HTML using ansi2html
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            subprocess.run(['ansi2html'], stdin=md_file, stdout=html_file, check=True)
        
        # Open the HTML file and remove lines containing "Progress:"
        with open(output_html_filepath, 'r') as html_file:
            lines = html_file.readlines()
        
        with open(output_html_filepath, 'w') as html_file:
            for line in lines:
                if "Progress:" not in line:
                    html_file.write(line)

        return output_md_filepath, output_html_filepath
    except subprocess.CalledProcessError as e:
        print_error_message(f"Error running FFUF for subdomains: {e}")
        return None, None
    except Exception as e:
        print_error_message(f"Error during HTML conversion: {e}")
        return None, None

def fuzz_vhosts(domain, target, port, notebook_dir):
    """Fuzz for virtual hosts using ffuf and convert output to HTML."""
    # Output filenames
    output_md_filename = f"027-webscan-{target}-{port}-ffuf_vhosts-output.md"
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)
    output_html_filename = f"027-webscan-{target}-{port}-ffuf_vhosts-output.html"
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)
    
    # FFUF command for virtual host fuzzing
    ffuf_command = [
        "ffuf",
        "-H", f"Host: FUZZ.{domain}",                  # Host header with FUZZ placeholder
        "-ac",                                         # Auto-calibrate to ignore baseline responses
        "-w", "/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt",      # Wordlist with FUZZ placeholder
        "-u", f"http://{domain}"                       # Target URL
    ]
    
    print_banner_message(f"Running Vhost Fuzzing: {RESET}{' '.join(ffuf_command)}")

    try:
        # Execute FFUF command and save output to the markdown file
        with open(output_md_filepath, 'w') as output_file:
            subprocess.run(ffuf_command, stdout=output_file, stderr=output_file, check=True)
        
        # Convert the markdown output to HTML using ansi2html
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            subprocess.run(['ansi2html'], stdin=md_file, stdout=html_file, check=True)
        
        # Remove lines containing "Progress:" from the HTML file
        with open(output_html_filepath, 'r') as html_file:
            lines = html_file.readlines()
        
        filtered_lines = [line for line in lines if "Progress:" not in line]
        
        with open(output_html_filepath, 'w') as html_file:
            html_file.writelines(filtered_lines)
        
        return output_md_filepath, output_html_filepath
    except subprocess.CalledProcessError as e:
        print_error_message(f"Error running FFUF for vhosts: {e}")
        return None, None
    except Exception as e:
        print_error_message(f"Error during HTML processing: {e}")
        return None, None

def run_eyewitness(domain, target, port):
    # Generate the filename in the current working directory
    filename = os.path.join(os.getcwd(), f"webscan-urls-{target}-{port}.md")
    
    # Build the EyeWitness command
    command = ["eyewitness", "--no-prompt", "-f", filename]

    if domain:
        # Run the command in the background, suppressing output
        full_command = f"{' '.join(command)} > /dev/null 2>&1 &"
    else:
        # Run the command normally, suppressing output
        full_command = f"{' '.join(command)} > /dev/null 2>&1"
    
    # Print the command being executed
    print_banner_message(f"Running Eyewitness: {RESET}{' '.join(command)}")

    
    # Execute the command
    subprocess.run(full_command, shell=True)

def copy_eyewitness_screens(notebook_dir, target, port):
    """Copy all files from the 'screens' directory in the most recent eyewitness folder to the notebook directory."""
    # Get the current year as a string
    current_year = str(datetime.now().year)
    
    # Retry logic for finding the directory
    retries = 10
    while retries > 0:
        # Find directories in the current working directory that start with the current year
        eyewitness_dirs = [
            d for d in os.listdir('.')
            if os.path.isdir(d) and d.startswith(current_year)
        ]
        
        if eyewitness_dirs:
            break
        
        # Wait 1 second before retrying
        retries -= 1
        if retries > 0:
            time.sleep(1)
        else:
            print("No eyewitness directories found after 10 retries.")
            return

    # Sort directories by modification time to find the most recent one
    eyewitness_dirs.sort(key=os.path.getmtime, reverse=True)
    most_recent_dir = eyewitness_dirs[0]
    
    # Define the source 'screens' directory
    screens_dir = os.path.join(most_recent_dir, "screens")
    if not os.path.exists(screens_dir):
        print(f"No 'screens' directory found in {most_recent_dir}.")
        return

    # Wait 15 seconds before starting the file copy process
    time.sleep(15)

    # Define the target directory in the notebook_dir
    target_dir = os.path.join(notebook_dir, f"00-eyewitness-{target}-{port}")
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy all files from the screens directory to the target directory
    for file_name in os.listdir(screens_dir):
        full_file_path = os.path.join(screens_dir, file_name)
        if os.path.isfile(full_file_path):
            shutil.copy(full_file_path, target_dir)

def run_aquatone(target, port):
    """Create a directory for Aquatone and run the Aquatone command using the webscan-urls file."""
    # Define filenames and directory
    url_output_filename = f"webscan-urls-{target}-{port}.md"
    aquatone_output_dir = f"aquatone-{target}-{port}"
    
    # Ensure the webscan-urls file exists
    if not os.path.exists(url_output_filename):
        raise FileNotFoundError(f"The file {url_output_filename} does not exist.")
    
    # Create the output directory if it doesn't exist
    os.makedirs(aquatone_output_dir, exist_ok=True)
    
    # Define the Aquatone command
    aquatone_command = f"cat {url_output_filename} | aquatone -out {aquatone_output_dir}/"
    
    # Print the banner message for the command (without executing it on the console)
    print_banner_message(f"Running Aquatone: {RESET}{aquatone_command}")
    
    # Execute the command, but suppress the output (no output displayed on the console)
    try:
        subprocess.run(aquatone_command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        #raise RuntimeError(f"Error running Aquatone: {e}")
        pass

def cleanup_geckodriver_log():
    """Remove the geckodriver.log file from the current directory if it exists."""
    log_file = "geckodriver.log"
    
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception:
            pass


def main():
    args = parse_arguments()
    '''
    print_banner_message(f"Target: {args.target}")
    print_banner_message(f"Port: {args.port}")
    print_banner_message(f"Web Path: {args.webpath}")
    print_banner_message(f"Is Domain: {args.domain}")
    print_banner_message(f"Full URL: {args.full_url}")
    '''
   
    print_banner_message(f"Analyzing target: {RESET}'{args.full_url}'")

    notebook_dir = create_notebook_directory()
    target_dir = get_target_directory(args.full_url)
    run_nmap_scan(args.target, args.port, notebook_dir)
    run_whatweb_scan(args.target, args.port, notebook_dir)
    run_wget(args.full_url)
    copy_site_to_notebook(target_dir, notebook_dir)
    run_ls_and_tee(target_dir, args.target, args.port, notebook_dir)
    run_feroxbuster(args.target, args.full_url, args.port, notebook_dir)
    run_ffuf(args.full_url, args.target, args.port, notebook_dir)
    run_gobuster(args.full_url, args.target, args.port, notebook_dir)
    convert_webscan_urls_to_html(args.target, args.port, notebook_dir)
    run_eyewitness(args.domain, args.target, args.port)
    copy_eyewitness_screens(notebook_dir, args.target, args.port)
    run_aquatone(args.target, args.port)
    cleanup_geckodriver_log()

    if args.domain:
        fuzz_subdomains(args.target, args.target, args.port, notebook_dir)
        fuzz_vhosts(args.target, args.target, args.port, notebook_dir)
    print_banner_message(f"{DARK_WHITE}Webscan Complete.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")


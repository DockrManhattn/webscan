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
BASE_NOTEBOOK_PATH = os.path.join(os.path.expanduser("~"), "notes", "Boxes")
#BASE_NOTEBOOK_PATH = "/path/to/your/obsidian/vault"

YELLOW = "\033[33m"
DARK_WHITE = "\033[2;37m"
BLUE = "\033[34m"
RESET = "\033[0m"

def print_informational_message(message):
    PRINT_INFORMATIONAL = f"{YELLOW}{{🌀🌵[+]🌵🌀}}{RESET}"
    print(f"{PRINT_INFORMATIONAL} {DARK_WHITE}{message}{RESET}")

def print_error_message(message):
    PRINT_ERROR = f"{YELLOW}{{💥💀🔥[+]🔥💀💥}}{RESET}"
    print(f"{PRINT_ERROR} {DARK_WHITE}{message}{RESET}")

def check_and_create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory {path} created.")
    else:
        return

def is_ip_address(value):
    try:
        socket.inet_aton(value)
        return True
    except socket.error:
        return False

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parse a URL or IP address.")
    parser.add_argument("target", help="The URL or IP address to analyze.")
    args = parser.parse_args()

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
    webpath = ""

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

    if ':' in target:
        target, port = target.split(":", 1)
        port = int(port) if port.isdigit() else default_port
    else:
        port = default_port

    return target, port, webpath

def create_notebook_directory():
    home_dir = os.path.expanduser("~")
    current_dir = os.getcwd()

    relative_path = os.path.relpath(current_dir, home_dir)

    notebook_dir = os.path.join(BASE_NOTEBOOK_PATH, relative_path)

    os.makedirs(notebook_dir, exist_ok=True)
    return notebook_dir

def run_command(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return stdout.decode()
        else:
            return stderr.decode()

    except Exception as e:
        return str(e)

def convert_md_to_html(md_file, notebook_dir):
    try:
        if not os.path.exists(md_file):
            raise FileNotFoundError(f"The file {md_file} does not exist.")

        html_file = os.path.join(notebook_dir, os.path.basename(md_file).replace('.md', '.html'))

        with open(md_file, 'r') as md_input:
            with open(html_file, 'w') as html_output:
                subprocess.run(['ansi2html'], stdin=md_input, stdout=html_output, check=True)

        return html_file  # Return the path of the newly created HTML file
    except Exception as e:
        return f"Error converting file {md_file} to HTML: {str(e)}"

def run_nmap_scan(target, port, notebook_dir):
    output_filename = f'020-webscan-{target}-{port}-nmap-http.md'
    nmap_command = [
        'nmap', '-sCV',
        '-script', 'http-webdav-scan.nse,http-userdir-enum.nse,http-shellshock.nse,http-robots.txt.nse,http-enum.nse,http-brute.nse',
        '-oN', output_filename,
        '-p', str(port), target
    ]
    command_str = " ".join(nmap_command)
    print_informational_message(f"Running Nmap: {RESET}{command_str}")

    process = subprocess.Popen(nmap_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        # Call the function to convert the .md file to .html
        html_file = convert_md_to_html(output_filename, notebook_dir)
        return stdout.decode(), html_file
    else:
        return stderr.decode(), None

def run_whatweb_scan(target, port, notebook_dir):    
    output_md_filename = f'021-webscan-{target}-{port}-whatweb-output.md'
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)  # Save .md in the current working directory
    output_html_filename = f'021-webscan-{target}-{port}-whatweb-output.html'
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)  # HTML in notebook_dir
    
    url = f"http://{target}" if port == 80 else f"http://{target}:{port}"
    
    whatweb_command = f"whatweb -v -a 3 {url} > {output_md_filepath}"
    
    shortened_command_display = f"whatweb -v -a 3 {url} > {output_md_filename}"
    print_informational_message(f"Running WhatWeb: {RESET}{shortened_command_display}")
    
    try:
        subprocess.run(whatweb_command, shell=True, check=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            ansi2html_command = ['ansi2html']
            process = subprocess.Popen(ansi2html_command, stdin=md_file, stdout=html_file)
            process.communicate()  # Wait for conversion to complete

        return output_md_filepath, output_html_filepath

    except subprocess.CalledProcessError as e:
        print_error_message(f"Error running WhatWeb scan or converting to HTML: {str(e)}")
        return None

def run_wget(url):
    wget_command = [
        "wget", "-r", "--level=0", "-E", "--ignore-length", "-x", "-k", "-p", 
        "--no-check-certificate", "-erobots=off", "-np", "-N", url
    ]
    print_informational_message(f"Running Wget: {RESET}{' '.join(wget_command)}")
    
    try:
        result = subprocess.run(wget_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    except subprocess.CalledProcessError as e:
        pass

def copy_site_to_notebook(target_dir, notebook_dir):
    try:
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            destination_dir = os.path.join(notebook_dir, os.path.basename(target_dir))
            
            if os.path.exists(destination_dir):
                shutil.rmtree(destination_dir)
            
            shutil.copytree(target_dir, destination_dir)
        else:
            print(f"Error: The target directory {target_dir} does not exist.")
    except Exception as e:
        print(f"Error occurred while copying: {e}")

def get_target_directory(url):
    target = re.sub(r'^https?://', '', url)  # Remove http:// or https://
    target = target.split('/')[0]  # Only the domain or IP (with port, if present)
    return target

def extract_hostname(url):
    hostname = re.sub(r'^https?://', '', url)
    hostname = hostname.split('/')[0]
    hostname = hostname.split(':')[0]
    return hostname

def run_ls_and_tee(target_dir, target, port, notebook_dir):    
    md_output_filename = f"022-webscan-{target}-{port}-wget-directory-output.md"
    
    ls_command = f"ls -lahR {target_dir} | tee {md_output_filename}"
    
    try:
        result = subprocess.run(ls_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if os.path.exists(md_output_filename):            
            html_file = convert_md_to_html(md_output_filename, notebook_dir)
        else:
            print(f"Error: Markdown file {md_output_filename} was not created.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")

def run_feroxbuster(target, url, port, notebook_dir):
    import os
    import subprocess

    hostname = extract_hostname(url)
    md_output_filename = f"023-webscan-{hostname}-{port}-ferox_basic_files.md"

    feroxbuster_command = [
        "feroxbuster",
        "-u", url,
        "-k",
        "--depth", "2",
        "--wordlist", os.path.expanduser("~/.local/bin/wordlists/common.txt"),
        "-s", "200", "302",
        "--threads", "150",
        "--extract-links",
        "-E",
        "-B",
        "-g",
        "-x", "php,html",
        "-o", md_output_filename
    ]

    try:
        print_informational_message(f"Running Feroxbuster: {RESET}{' '.join(feroxbuster_command)}")
        with open(md_output_filename, 'w') as output_file:
            subprocess.run(feroxbuster_command, stdout=output_file, stderr=subprocess.DEVNULL, check=True, text=True)
        
        # Convert Markdown to HTML
        html_output = convert_md_to_html(md_output_filename, notebook_dir)

    except subprocess.CalledProcessError as e:
        print(f"Error running feroxbuster: {e}")
    except Exception as e:
        print(f"Error during processing: {e}")


def run_ffuf(url, target, port, notebook_dir):    
    output_filename = f"024-webscan-{target}-{port}-ffuf_wordlist.md"
    url = url.rstrip("/")

    ffuf_command = [
        "ffuf",
        "-u", f"{url}/FUZZ",
        "-w", os.path.expanduser("~/.local/bin/wordlists/directory-list-2.3-medium.txt"),
        "-ac",
        "-v",
        "-t", "150"
    ]
    
    try:
        print_informational_message(f"Running FFUF: {RESET}{' '.join(ffuf_command)}")
        with open(output_filename, 'w') as output_file:
            subprocess.run(ffuf_command, stdout=output_file, stderr=subprocess.DEVNULL, check=True, text=True)

        html_output = convert_md_to_html(output_filename, notebook_dir)
    
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running ffuf: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def run_gobuster(full_url, target, port, notebook_dir):
    if not target or not port:
        raise ValueError("Target and port must be defined")

    output_file = f"025-webscan-{target}-{port}-gobuster_wc_big.md"

    gobuster_command = [
        "gobuster", "dir",
        "-w", os.path.expanduser("~/.local/bin/wordlists/big.txt"),
        "-x", "php,txt,html,jpg",
        "-t", "150",
        "-q", "-n", "-e", "-k",
        "-u", full_url,
        "--no-error"
    ]

    try:
        print_informational_message(f"Running Gobuster: {RESET}{' '.join(gobuster_command)}")
        with open(output_file, 'w') as output_f:
            subprocess.run(gobuster_command, stdout=output_f, stderr=subprocess.DEVNULL, check=True, text=True)

    except subprocess.CalledProcessError as e:
        print(f"Error running gobuster: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")



def process_webscan_files(target, port):
    output_file = f'webscan-urls-{target}-{port}.md'
    unique_urls = set()
    
    file_mappings = {
        '023': f'023-webscan-{target}-{port}-ferox_basic_files.md',
        '024': f'024-webscan-{target}-{port}-ffuf_wordlist.md',
        '025': f'025-webscan-{target}-{port}-gobuster_wc_big.md'
    }

    for prefix, filename in file_mappings.items():
        try:
            with open(filename, 'r') as file:
                for line in file:
                    url = ''
                    if prefix == '023':  # Feroxbuster
                        parts = line.split()
                        if len(parts) > 5:
                            url = parts[5]

                    elif prefix == '024':  # FFUF
                        if 'http' in line:
                            parts = line.split()
                            if len(parts) > 3:
                                url = parts[3]

                    elif prefix == '025':  # Gobuster
                        parts = line.split()
                        if len(parts) > 0:
                            url = parts[0]

                    if url:
                        #print(f"Extracted URL from {filename}: {url}")  # Debugging
                        unique_urls.add(url)
        except FileNotFoundError:
            print(f"File {filename} not found, skipping.")
            continue

    with open(output_file, 'w') as file:
        for url in unique_urls:
            file.write(url + '\n')
    
    print(f"Extracted {len(unique_urls)} unique URLs and wrote to {output_file}")



def convert_webscan_urls_to_html(target, port, notebook_dir):
    url_output_filename = f"webscan-urls-{target}-{port}.md"
    
    if not os.path.isfile(url_output_filename):
        print(f"Error: The file {url_output_filename} does not exist.")
        
        # Run the cat | awk command here if needed (assuming you want to process a different file)
        file_path = '023-webscan-clipbucket.local-80-ferox_basic_files.md'
        try:
            # Running the shell command directly
            command = f"cat {file_path} | awk '{{print $6}}'"
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Print the result of the command
            print(result.stdout)
        
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running awk command: {e.stderr}")
        
        # Return None after handling the error
        return None

    with open(url_output_filename, 'r') as file:
        lines = file.readlines()

    unique_lines = list(set(lines))

    with open(url_output_filename, 'w') as file:
        file.writelines(unique_lines)

    output_html_file = os.path.join(notebook_dir, f"webscan-urls-{target}-{port}.html")
    ansi2html_command = f"ansi2html < {url_output_filename} > {output_html_file}"
    subprocess.run(ansi2html_command, shell=True, check=True)

    return output_html_file

def fuzz_subdomains(domain, target, port, notebook_dir):
    output_md_filename = f"026-webscan-{target}-{port}-ffuf-subdomains-output.md"
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)
    output_html_filename = f"026-webscan-{target}-{port}-ffuf-subdomains-output.html"
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)
    
    ffuf_command = [
        "ffuf",
        "-w", os.path.expanduser("~/.local/bin/wordlists/dnslist.txt:FUZZ"),  # Wordlist with FUZZ placeholder
        "-u", f"http://FUZZ.{domain}",                 # Target URL with subdomain placeholder
        "-mc", "all", 
        "-t", "150",                                   # Threads
    ]
    
    print_informational_message(f"Running Subdomain Fuzzing: {RESET}{' '.join(ffuf_command)}")

    try:
        with open(output_md_filepath, 'w') as output_file:
            subprocess.run(ffuf_command, stdout=output_file, stderr=output_file, check=True)
        
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            subprocess.run(['ansi2html'], stdin=md_file, stdout=html_file, check=True)
        
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
    # Output filenames
    output_md_filename = f"027-webscan-{target}-{port}-ffuf_vhosts-output.md"
    output_md_filepath = os.path.join(os.getcwd(), output_md_filename)
    output_html_filename = f"027-webscan-{target}-{port}-ffuf_vhosts-output.html"
    output_html_filepath = os.path.join(notebook_dir, output_html_filename)
    
    ffuf_command = [
        "ffuf",
        "-H", f"Host: FUZZ.{domain}",                  # Host header with FUZZ placeholder
        "-ac",
        "-mc", "all",                                         # Auto-calibrate to ignore baseline responses
        "-w", os.path.expanduser("~/.local/bin/wordlists/dnslist.txt"),      # Wordlist with FUZZ placeholder
        "-u", f"http://{domain}"                       # Target URL
    ]
    
    print_informational_message(f"Running Vhost Fuzzing: {RESET}{' '.join(ffuf_command)}")

    try:
        with open(output_md_filepath, 'w') as output_file:
            subprocess.run(ffuf_command, stdout=output_file, stderr=output_file, check=True)
        
        with open(output_md_filepath, 'r') as md_file, open(output_html_filepath, 'w') as html_file:
            subprocess.run(['ansi2html'], stdin=md_file, stdout=html_file, check=True)
        
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
    filename = os.path.join(os.getcwd(), f"webscan-urls-{target}-{port}.md")
    
    command = ["eyewitness", "--no-prompt", "-f", filename]

    if domain:
        full_command = f"{' '.join(command)} > /dev/null 2>&1 &"
    else:
        full_command = f"{' '.join(command)} > /dev/null 2>&1"
    
    print_informational_message(f"Running Eyewitness: {RESET}{' '.join(command)}")

    subprocess.run(full_command, shell=True)

def copy_eyewitness_screens(notebook_dir, target, port):
    current_year = str(datetime.now().year)
    
    retries = 10
    while retries > 0:
        eyewitness_dirs = [
            d for d in os.listdir('.')
            if os.path.isdir(d) and d.startswith(current_year)
        ]
        
        if eyewitness_dirs:
            break
        
        retries -= 1
        if retries > 0:
            time.sleep(1)
        else:
            print("No eyewitness directories found after 10 retries.")
            return

    eyewitness_dirs.sort(key=os.path.getmtime, reverse=True)
    most_recent_dir = eyewitness_dirs[0]
    
    screens_dir = os.path.join(most_recent_dir, "screens")
    if not os.path.exists(screens_dir):
        print(f"No 'screens' directory found in {most_recent_dir}.")
        return

    time.sleep(15)

    target_dir = os.path.join(notebook_dir, f"00-eyewitness-{target}-{port}")
    os.makedirs(target_dir, exist_ok=True)
    
    for file_name in os.listdir(screens_dir):
        full_file_path = os.path.join(screens_dir, file_name)
        if os.path.isfile(full_file_path):
            shutil.copy(full_file_path, target_dir)

def run_aquatone(target, port):
    url_output_filename = f"webscan-urls-{target}-{port}.md"
    aquatone_output_dir = f"aquatone-{target}-{port}"
    
    # Ensure the webscan-urls file exists
    if not os.path.exists(url_output_filename):
        raise FileNotFoundError(f"The file {url_output_filename} does not exist.")
    
    # Create the output directory if it doesn't exist
    os.makedirs(aquatone_output_dir, exist_ok=True)
    
    # Define the Aquatone command
    aquatone_command = f"cat {url_output_filename} | aquatone -out {aquatone_output_dir}/"
    
    # Print the PRINT_INFORMATIONAL message for the command (without executing it on the console)
    print_informational_message(f"Running Aquatone: {RESET}{aquatone_command}")
    
    # Execute the command, but suppress the output (no output displayed on the console)
    try:
        subprocess.run(aquatone_command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        pass

def cleanup_geckodriver_log():
    log_file = "geckodriver.log"
    
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception:
            pass

def main():
    args = parse_arguments()
   
    print_informational_message(f"Analyzing target: {RESET}'{args.full_url}'")

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
    process_webscan_files(args.target, args.port)
    convert_webscan_urls_to_html(args.target, args.port, notebook_dir)
    run_eyewitness(args.domain, args.target, args.port)
    copy_eyewitness_screens(notebook_dir, args.target, args.port)
    run_aquatone(args.target, args.port)
    cleanup_geckodriver_log()

    if args.domain:
        fuzz_subdomains(args.target, args.target, args.port, notebook_dir)
        fuzz_vhosts(args.target, args.target, args.port, notebook_dir)
    print_informational_message(f"{DARK_WHITE}Webscan Complete.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")

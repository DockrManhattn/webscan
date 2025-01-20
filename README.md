# Webscan

# Installation
If you have seclists installed, cool.  If you don't have seclists installed as either /usr/share/seclists or /usr/share/SecLists than this is going to take some time because it will become installed.  The setup will also prompt for a password again at the end where it's moving a staging directory from /tmp to /usr/share/seclists.
```bash
python3 setup.py
alias webscan='python3 /path/to/webscan.py'
```
If you have an obsidian notebook be sure to check out these lines in the script:
```bash
# Base directory for obsidian vault
BASE_NOTEBOOK_PATH = os.path.join(os.path.expanduser("~"), "notes", "Boxes")
#BASE_NOTEBOOK_PATH = "/path/to/your/obsidian/vault"
```
If you define your notebook path here, the script will automatically move files as html into the path.  With obsidian I use the plugin "htmlreader" to get the best user experience.
# Usage
```bash
python3 webscan.py 'http://srv.tea.vl:3000'
```

# Example
```bash
┌─[kali@parrot]─[~]
└──╼ $export URL='http://srv.tea.vl:3000'
┌─[kali@parrot]─[~/webscan_demo]
└──╼ $webscan $URL
{🌀🌵[+]🌵🌀} Analyzing target: 'http://srv.tea.vl:3000'
{🌀🌵[+]🌵🌀} Running Nmap: nmap -sCV -script http-webdav-scan.nse,http-userdir-enum.nse,http-shellshock.nse,http-robots.txt.nse,http-enum.nse,http-brute.nse -oN 020-webscan-srv.tea.vl-3000-nmap-http.md -p 3000 srv.tea.vl
{🌀🌵[+]🌵🌀} Running WhatWeb: whatweb -v -a 3 http://srv.tea.vl:3000 > 021-webscan-srv.tea.vl-3000-whatweb-output.md
{🌀🌵[+]🌵🌀} Running Wget: wget -r --level=0 -E --ignore-length -x -k -p --no-check-certificate -erobots=off -np -N http://srv.tea.vl:3000
{🌀🌵[+]🌵🌀} Running Feroxbuster: feroxbuster -u http://srv.tea.vl:3000 -k --depth 2 --wordlist /usr/share/wordlists/dirb/common.txt -s 200 302 --threads 150 --extract-links -E -B -g -x php,html -o 023-webscan-srv.tea.vl-3000-ferox_basic_files.md
{🌀🌵[+]🌵🌀} Running Ffuf: ffuf -u http://srv.tea.vl:3000/FUZZ -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -ac -v -t 150
{🌀🌵[+]🌵🌀} Running Gobuster: gobuster dir -w /usr/share/seclists/Discovery/Web-Content/big.txt -x php,txt,html,jpg -t 150 -q -n -e -u http://srv.tea.vl:3000 --no-error
{🌀🌵[+]🌵🌀} Running Eyewitness: eyewitness --no-prompt -f /home/kali/webscan_demo/webscan-urls-srv.tea.vl-3000.md
{🌀🌵[+]🌵🌀} Running Aquatone: cat webscan-urls-srv.tea.vl-3000.md | aquatone -out aquatone-srv.tea.vl-3000/
{🌀🌵[+]🌵🌀} Running Subdomain Fuzzing: ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt:FUZZ -u http://FUZZ.srv.tea.vl -t 150
{🌀🌵[+]🌵🌀} Running Vhost Fuzzing: ffuf -H Host: FUZZ.srv.tea.vl -ac -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://srv.tea.vl
{🌀🌵[+]🌵🌀} Webscan Complete.

┌─[✗]─[kali@parrot]─[~/webscan_demo]
└──╼ $ls -lah
total 204K
drwxr-xr-x 1 kali kali  928 Jan  7 11:30 .
drwxr-xr-x 1 kali kali  802 Jan  7 11:27 ..
-rw-r--r-- 1 kali kali 4.7K Jan  7 11:15 020-webscan-srv.tea.vl-3000-nmap-http.md
-rw-r--r-- 1 kali kali 2.7K Jan  7 11:16 021-webscan-srv.tea.vl-3000-whatweb-output.md
-rw-r--r-- 1 kali kali  15K Jan  7 11:17 022-webscan-srv.tea.vl-3000-wget-directory-output.md
-rw-r--r-- 1 kali kali 2.1K Jan  7 11:18 023-webscan-srv.tea.vl-3000-ferox_basic_files.md
-rw-r--r-- 1 kali kali 3.3K Jan  7 11:23 024-webscan-srv.tea.vl-3000-ffuf_wordlist.md
-rw-r--r-- 1 kali kali  667 Jan  7 11:27 025-webscan-srv.tea.vl-3000-gobuster_wc_big.md
-rw-r--r-- 1 kali kali  93K Jan  7 11:30 026-webscan-srv.tea.vl-3000-ffuf-subdomains-output.md
-rw-r--r-- 1 kali kali  57K Jan  7 11:31 027-webscan-srv.tea.vl-3000-ffuf_vhosts-output.md
drwxr-xr-x 1 kali kali  202 Jan  7 11:28 2025-01-07_112729
drwxr-xr-x 1 kali kali  160 Jan  7 11:28 aquatone-srv.tea.vl-3000
drwxr-xr-x 1 kali kali 3.0K Jan  7 11:17 srv.tea.vl:3000
-rw-r--r-- 1 kali kali  526 Jan  7 11:27 webscan-urls-srv.tea.vl-3000.md
```
Eyewitness folder looks like: 2025-01-07_112729
Aquatone folder looks like: aquatone-srv.tea.vl-3000
URLs identified are in: webscan-urls-srv.tea.vl-3000.md

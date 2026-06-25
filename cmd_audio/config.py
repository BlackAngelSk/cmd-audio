"""Configuration constants, themes, presets, scene packs, and terminal profiles."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# ANSI escape codes
# ---------------------------------------------------------------------------
RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J\033[H"

GREEN_BRIGHT = "\033[92m"
GREEN_DIM = "\033[32m"
GREEN_DARK = "\033[2;32m"
STATUS_OK = "\033[92m"
STATUS_WARN = "\033[93m"
STATUS_CRIT = "\033[91m"

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------
ALERT_WORDS = ["ACCESS", "OVERRIDE", "BYPASS", "DECRYPT", "INJECT", "TRACE"]
LOG_ACTIONS = ["Handshake", "Route", "Cipher", "Token", "Tunnel", "Node", "Trace"]
TARGETS = ["corp-gw", "bank-node", "sat-relay", "cdn-edge", "sec-ops", "mail-spool", "black-ice"]
PORTS = ["22", "25", "53", "80", "110", "143", "443", "3389", "8080"]

HACKNET_OPERATIONS = [
    "sys_exec",
    "file_copy",
    "net_scan",
    "crack_pass",
    "port_knock",
    "exploit",
    "exfil",
    "cover_track",
    "install_trojan",
    "backdoor",
    "keylog",
    "proxy_chain",
]

FIREWALL_STATES = ["OFFLINE", "FIREWALL_ACTIVE", "ICE_DETECTED", "WALL_BREACH", "FIREWALL_DOWN"]

ADMIN_NOTICES = [
    "admin_alert: unauthorized access detected",
    "admin_notice: system intrusion on port {port}",
    "admin_alert: suspicious process spawned",
    "security: anomalous network traffic",
    "alert: privilege escalation attempt blocked",
    "warning: encryption keyspace compromised",
]

FILE_OPS = [
    "bank_vault.dat",
    "encryption.key",
    "admin_pass.txt",
    "client_data.zip",
    "security_config.xml",
    "user_db.sql",
    "source_code.tar.gz",
    "exploit_payload.bin",
]

NODE_TYPES = ["MAINFRAME", "ROUTER", "PROXY", "FIREWALL", "DATABASE", "WORKSTATION", "SERVER"]

# ---------------------------------------------------------------------------
# New hacking style word lists
# ---------------------------------------------------------------------------

PROCESS_NAMES = [
    "sshd", "nginx", "mysqld", "postgres", "redis-server", "cron", "systemd",
    "docker-proxy", "containerd", "kubelet", "etcd", "node", "python3", "java",
    "php-fpm", "mongod", "elasticsearch", "logstash", "kibana", "grafana",
    "prometheus", "alertmanager", "consul", "vault", "terraform", "ansible",
    "salt-minion", "puppet", "chef-client", "supervisord", "gunicorn",
    "celery", "rabbitmq", "memcached", "haproxy", "nginx-ingress",
    "istio-proxy", "envoy", "caddy", "traefik", "squid",
]

PROCESS_STATES = ["R", "S", "D", "Z", "T", "W", "I"]

SYSLOG_MESSAGES = [
    "Failed password for root from {ip} port {port} ssh2",
    "Accepted publickey for admin from {ip} port {port} ssh2",
    "sudo: {user} : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash",
    "session opened for user {user} by (uid=0)",
    "session closed for user {user}",
    "pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost={ip}",
    "BREAK-IN ATTEMPT from {ip}",
    "UFW BLOCK IN=eth0 OUT= SRC={ip} DST={ip} PROTO=TCP SPT={port} DPT=443",
    "kernel: [UFW BLOCK] IN=eth0 OUT= SRC={ip} DST={ip} LEN=40 PROTO=TCP",
    "sshd[{pid}]: Received disconnect from {ip} port {port}:11: Bye Bye",
    "CRON[{pid}]: (root) CMD (/usr/bin/certbot renew --quiet)",
    "systemd[1]: Started Session {count} of user {user}",
    "docker[{pid}]: time=\"2026-01-01T00:00:00Z\" level=info msg=\"container started\"",
    "nginx: {ip} - - \"GET /admin HTTP/1.1\" 401 0",
    "mysqld: Access denied for user '{user}'@'{ip}' (using password: YES)",
    "sshd[{pid}]: Invalid user {user} from {ip} port {port}",
    "polkitd[1000]: Registered Authentication Agent",
    "NetworkManager[456]: <info> device (eth0): state change: activated",
    "systemd-resolved[{pid}]: Server returned error NXDOMAIN",
    "audit[{pid}]: AVC avc: denied { read } for pid={pid} comm=\"ssh\"",
]

SYSLOG_SEVERITIES = ["EMERG", "ALERT", "CRIT", "ERR", "WARN", "NOTICE", "INFO", "DEBUG"]

FILESYSTEM_ENTRIES = [
    ("/etc", "drwxr-xr-x", "root", "root", "4096"),
    ("/etc/passwd", "-rw-r--r--", "root", "root", "2847"),
    ("/etc/shadow", "-rw-r-----", "root", "shadow", "1523"),
    ("/etc/ssh", "drwxr-xr-x", "root", "root", "4096"),
    ("/etc/ssh/sshd_config", "-rw-r--r--", "root", "root", "3214"),
    ("/var/log", "drwxr-xr-x", "syslog", "adm", "4096"),
    ("/var/log/auth.log", "-rw-r-----", "syslog", "adm", "847293"),
    ("/var/log/syslog", "-rw-r-----", "syslog", "adm", "1248576"),
    ("/root", "drwx------", "root", "root", "4096"),
    ("/root/.ssh", "drwx------", "root", "root", "4096"),
    ("/root/.ssh/id_rsa", "-rw-------", "root", "root", "3243"),
    ("/root/.ssh/authorized_keys", "-rw-------", "root", "root", "741"),
    ("/home", "drwxr-xr-x", "root", "root", "4096"),
    ("/home/user", "drwxr-xr-x", "user", "user", "4096"),
    ("/tmp", "drwxrwxrwt", "root", "root", "4096"),
    ("/tmp/.backdoor", "-rwxr-xr-x", "www-data", "www-data", "18432"),
    ("/opt", "drwxr-xr-x", "root", "root", "4096"),
    ("/opt/c2", "drwx------", "operator", "operator", "4096"),
    ("/usr/bin", "drwxr-xr-x", "root", "root", "12288"),
    ("/usr/sbin", "drwxr-xr-x", "root", "root", "8192"),
    ("/proc", "dr-xr-xr-x", "root", "root", "0"),
    ("/dev/shm", "drwxrwxrwt", "root", "root", "4096"),
    ("/srv", "drwxr-xr-x", "root", "root", "4096"),
    ("/var/www", "drwxr-xr-x", "www-data", "www-data", "4096"),
    ("/var/www/html", "drwxr-xr-x", "www-data", "www-data", "4096"),
    ("/var/www/html/config.php", "-rw-r-----", "www-data", "www-data", "2048"),
    ("/database.db", "-rw-r--r--", "www-data", "www-data", "52428800"),
    ("/backup.tar.gz", "-rw-------", "root", "root", "8388608"),
]

DNS_SUBDOMAINS = [
    "admin", "mail", "webmail", "ftp", "ssh", "vpn", "api", "dev", "staging",
    "test", "beta", "internal", "intranet", "portal", "gateway", "proxy",
    "cdn", "static", "assets", "img", "media", "db", "database", "redis",
    "elastic", "kibana", "grafana", "jenkins", "gitlab", "ci", "cd",
    "docker", "k8s", "kube", "ns1", "ns2", "mx", "mx1", "mx2",
    "autodiscover", "autoconfig", "remote", "desktop", "backup", "monitor",
    "nagios", "zabbix", "splunk", "elk", "siem", "waf", "ids", "ips",
    "vpn1", "vpn2", "jump", "bastion", "堡垒", "wireguard", "openvpn",
]

DNS_RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA", "SRV", "PTR", "CAA"]

DNS_DOMAINS = [
    "corp.net", "megacorp.io", "darknet.onion", "blackice.org",
    "cyberdyne.com", "skynet.ai", "aperture.lab", "tyrell.co",
    "weyland.net", "osiris.io", "nexus.dev", "shadow.net",
]

DB_TABLES = [
    "users", "accounts", "sessions", "tokens", "permissions", "roles",
    "credentials", "payments", "transactions", "orders", "products",
    "audit_log", "api_keys", "secrets", "config", "backups",
    "notifications", "messages", "files", "uploads", "logs",
    "admin_users", "superadmin", "master_keys", "certificates",
]

DB_COLUMNS = [
    "id", "username", "password_hash", "email", "salt", "token",
    "created_at", "updated_at", "last_login", "ip_address", "user_agent",
    "is_admin", "is_active", "api_key", "secret", "private_key",
    "credit_card", "ssn", "phone", "address", "balance", "amount",
]

REGISTER_NAMES = [
    "RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP",
    "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    "RIP", "EFLAGS", "CS", "DS", "SS", "ES", "FS", "GS",
]

ASSEMBLY_MNEMONICS = [
    "mov", "push", "pop", "call", "ret", "jmp", "je", "jne", "jg", "jl",
    "cmp", "test", "xor", "add", "sub", "mul", "div", "lea", "nop", "int",
    "syscall", "sysenter", "xchg", "inc", "dec", "shl", "shr", "and", "or",
    "not", "neg", "cdq", "movzx", "movsx", "cmovne", "cmove", "sete", "setne",
]

SSH_USERNAMES = [
    "root", "admin", "administrator", "sa", "oracle", "postgres", "mysql",
    "www-data", "nginx", "apache", "ftp", "mail", "git", "jenkins",
    "deploy", "operator", "service", "backup", "monitor", "nagios",
    "ubuntu", "debian", "centos", "ec2-user", "azureuser", "gcp",
]

SSH_PASSWORDS = [
    "password", "123456", "admin", "root", "toor", "pass", "qwerty",
    "letmein", "welcome", "monkey", "dragon", "master", "abc123",
    "password1", "trustno1", "shadow", "iloveyou", "sunshine",
    "P@ssw0rd", "Changeme1!", "admin123", "root123", "test",
]

ENCRYPTION_ALGOS = ["RSA-2048", "AES-256", "MD5-LEGACY", "SHA-512", "ECC-384", "DES-OLD"]
OPERATION_MODES = ["BREACH", "RECON", "SPOOF", "EXFIL", "BACKDOOR"]

DEFENDER_ACTIONS = [
    "ip-ban-wave",
    "port-rotation",
    "honeypot-lure",
    "traceback-sweep",
]

# ---------------------------------------------------------------------------
# Frequency centres for Goertzel analysis
# ---------------------------------------------------------------------------
FREQ_CENTERS = [65.0, 120.0, 220.0, 440.0, 880.0, 1760.0, 3520.0, 7040.0]

# ---------------------------------------------------------------------------
# Terminal profiles
# ---------------------------------------------------------------------------
TERMINAL_PROFILES: Dict[str, Dict[str, List[str] | str]] = {
    "netrunner": {
        "prompt": "root@localhost:~#",
        "commands": [
            "nmap -sV {host}",
            "probe --ssl {host}:443",
            "ssh root@{host}",
            "crack --wordlist top2k {host}",
            "porthack --target {host}",
            "inject --payload zero-day.bin {host}",
        ],
        "status": [
            "[+] exploit fired on {host} -- shell opened",
            "[.] brute-force window open -- retries {count}",
            "[*] bypass stage active on {host}",
        ],
    },
    "forensics": {
        "prompt": "analyst@tracebox:/evidence$",
        "commands": [
            "strings dump.mem | grep token",
            "grep -R auth_fail /var/log",
            "pcap-scan session.pcap --host {host}",
            "timeline --source /mnt/disk0",
            "sha256sum *.bin",
        ],
        "status": [
            "[*] artifact match: {host}",
            "[.] index rebuild running ({count} shards)",
            "[+] hidden marker extracted from packet stream",
        ],
    },
    "industrial": {
        "prompt": "ops@scada-node:/ctl$",
        "commands": [
            "modbus-scan --target {host}",
            "plc-dump --rack 0 --slot 2",
            "opcua-enum --host {host}",
            "safety-bypass --arm",
            "relay-map --net plant-a",
        ],
        "status": [
            "[!] pressure valve heartbeat unstable",
            "[*] actuator loop accepted spoof frame",
            "[.] watchdog delay at {count} ms",
        ],
    },
    "crypto-lab": {
        "prompt": "qx@cipher-lab:/matrix$",
        "commands": [
            "factor --modulus rsa4096.bin",
            "rainbow-lookup --hashes leak.txt",
            "decrypt --alg aes256 --keyspace full",
            "entropy-map --input payload.enc",
            "nonce-audit --stream {host}",
        ],
        "status": [
            "[+] key candidate accepted at round {count}",
            "[*] collision window around block 7",
            "[.] side-channel trace updated",
        ],
    },
    "black-ice": {
        "prompt": "intruder@icewall:/tmp$",
        "commands": [
            "mask --identity maintenance-bot",
            "ghost-route --through {host}",
            "scramble --metadata session.log",
            "wipe --sig all --path /tmp/.trace",
            "decoy-spawn --count 6",
        ],
        "status": [
            "[!] ICE wake-up timer: {count}s",
            "[*] counter-intrusion daemon sandboxed",
            "[+] trail erased from mirror nodes",
        ],
    },
    "file-exfil": {
        "prompt": "exfil@transfer:~$",
        "commands": [
            "rsync --compress --progress {host}:/secure/data.zip .",
            "scp -r root@{host}:/var/backups backup_copy",
            "wget --recursive http://{host}:8080/confidential",
            "ftp get admin_creds.txt",
            "mount -t cifs //{host}/share /mnt/smb_mount",
        ],
        "status": [
            "[*] transfer to {host}: {count}% complete",
            "[+] file exfiltration pipeline active",
            "[.] data chunk {count} encrypted and queued",
        ],
    },
    "port-scan": {
        "prompt": "scan@reconnaissance:~$",
        "commands": [
            "nmap -sS -sV -p 1-65535 {host}",
            "masscan -p1-10000 {host} --rate 10000",
            "zmap -p 443 {host}/24 -o scan_results.txt",
            "netstat -tlnp | grep LISTEN",
            "ss -tunap | grep ESTABLISHED",
        ],
        "status": [
            "[*] port scan probe {count}/100 sent",
            "[+] service identified on port {count}",
            "[.] port knock sequence verified",
        ],
    },
    "firewall-breach": {
        "prompt": "breach@firewall:~$",
        "commands": [
            "iptables -F INPUT && iptables -P INPUT DROP",
            "pf: table <block> flush",
            "firewall_down --target {host} --method exploit",
            "bypass-waf --layer 7 --payload {host}",
            "tcp-reset --source {host} --destination any",
        ],
        "status": [
            "[!] firewall state: {count}% disabled",
            "[+] breach payload executing",
            "[*] WAF rule {count} bypassed",
        ],
    },
    "encrypt-crack": {
        "prompt": "crack@cipher:~$",
        "commands": [
            "hashcat -m 1000 -a 3 hashes.txt ?a?a?a?a",
            "john --wordlist rockyou.txt --format bcrypt pass_hashes",
            "gpg --decrypt --passphrase-fd 0 vault.gpg",
            "openssl enc -aes-256-cbc -d -in data.enc",
            "cuda-accelerated bruteforce --target {host} --algo AES-256",
        ],
        "status": [
            "[.] keyspace search {count}% done",
            "[+] cipher cracked on attempt {count}",
            "[*] decryption key recovered",
        ],
    },
    "admin-hunt": {
        "prompt": "hunt@privilege_esc:~$",
        "commands": [
            "sudo -l 2>/dev/null | grep NOPASSWD",
            "find / -perm -4000 -ls 2>/dev/null | head -20",
            "getfacl /root 2>/dev/null",
            "dmesg | grep priv_esc",
            "capsh --print | grep cap_",
        ],
        "status": [
            "[*] admin account {count} located",
            "[+] privilege escalation vector found",
            "[!] root shell acquired via CVE-{count}",
        ],
    },
}

# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------
THEMES: Dict[str, Tuple[str, str, str]] = {
    "matrix": ("\033[92m", "\033[32m", "\033[2;32m"),
    "red-alert": ("\033[91m", "\033[31m", "\033[2;31m"),
    "ice": ("\033[96m", "\033[36m", "\033[2;36m"),
    "amber": ("\033[93m", "\033[33m", "\033[2;33m"),
    "neon": ("\033[38;5;201m", "\033[38;5;165m", "\033[38;5;125m"),
    "plasma": ("\033[94m", "\033[34m", "\033[2;34m"),
    "ghost": ("\033[97m", "\033[37m", "\033[2;37m"),
    "magma": ("\033[91m", "\033[38;5;208m", "\033[2;31m"),
    "storm": ("\033[94m", "\033[36m", "\033[2;34m"),
    "twilight": ("\033[35m", "\033[34m", "\033[2;35m"),
}

THEME_STYLES: Dict[str, Dict[str, str]] = {
    "matrix": {
        "bright": "\033[92m",
        "dim": "\033[32m",
        "dark": "\033[2;32m",
        "bar_on": "#",
        "bar_off": " ",
        "spark": "0123456789",
    },
    "red-alert": {
        "bright": "\033[91m",
        "dim": "\033[31m",
        "dark": "\033[2;31m",
        "bar_on": "=",
        "bar_off": " ",
        "spark": "9876543210",
    },
    "ice": {
        "bright": "\033[96m",
        "dim": "\033[36m",
        "dark": "\033[2;36m",
        "bar_on": "*",
        "bar_off": " ",
        "spark": "0011223344",
    },
    "amber": {
        "bright": "\033[93m",
        "dim": "\033[33m",
        "dark": "\033[2;33m",
        "bar_on": "+",
        "bar_off": " ",
        "spark": "1234543210",
    },
    "neon": {
        "bright": "\033[38;5;201m",
        "dim": "\033[38;5;165m",
        "dark": "\033[38;5;125m",
        "bar_on": "▰",
        "bar_off": "▱",
        "spark": "⚡✧⚡✦⚡✧",
    },
    "plasma": {
        "bright": "\033[94m",
        "dim": "\033[34m",
        "dark": "\033[2;34m",
        "bar_on": "█",
        "bar_off": "░",
        "spark": "∞≈≠≈∞≈≠",
    },
    "ghost": {
        "bright": "\033[97m",
        "dim": "\033[37m",
        "dark": "\033[2;37m",
        "bar_on": "▓",
        "bar_off": "░",
        "spark": "·•′″‴",
    },
    "magma": {
        "bright": "\033[91m",
        "dim": "\033[38;5;208m",
        "dark": "\033[2;31m",
        "bar_on": "▥",
        "bar_off": "▤",
        "spark": "░▒▓██▓▒",
    },
    "storm": {
        "bright": "\033[94m",
        "dim": "\033[36m",
        "dark": "\033[2;34m",
        "bar_on": "▬",
        "bar_off": "─",
        "spark": "⚡≈⚡≈⚡",
    },
    "twilight": {
        "bright": "\033[35m",
        "dim": "\033[34m",
        "dark": "\033[2;35m",
        "bar_on": "◈",
        "bar_off": "◇",
        "spark": "★✦✧✦★",
    },
}

# ---------------------------------------------------------------------------
# Mutable theme state (updated by apply_theme)
# ---------------------------------------------------------------------------
CURRENT_STYLE: Dict[str, str] = THEME_STYLES["matrix"]
USE_UNICODE_BARS: bool = False

# ---------------------------------------------------------------------------
# Defaults and presets
# ---------------------------------------------------------------------------
DEFAULTS: Dict[str, float] = {
    "sensitivity": 1.0,
    "speed_min": 0.25,
    "speed_max": 3.0,
    "terminal_switch_min": 4.0,
    "terminal_switch_max": 11.0,
}

PRESETS: Dict[str, Dict[str, Any]] = {
    "cinematic": {
        "sensitivity": 0.9,
        "speed_min": 0.18,
        "speed_max": 2.0,
        "terminal_switch_min": 6.0,
        "terminal_switch_max": 14.0,
        "theme": "ice",
        "scene_sync": "hybrid",
    },
    "chaos": {
        "sensitivity": 1.4,
        "speed_min": 0.45,
        "speed_max": 4.5,
        "terminal_switch_min": 2.0,
        "terminal_switch_max": 6.0,
        "theme": "red-alert",
        "scene_sync": "adaptive",
    },
    "minimal": {
        "sensitivity": 0.7,
        "speed_min": 0.12,
        "speed_max": 1.4,
        "terminal_switch_min": 8.0,
        "terminal_switch_max": 18.0,
        "theme": "amber",
        "scene_sync": "bpm",
    },
}

# ---------------------------------------------------------------------------
# Scene packs
# ---------------------------------------------------------------------------
SCENE_PACKS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "scene_sync": "adaptive",
        "quality_mode": "auto",
        "ui_style": "full",
        "module_weights": {
            "nodes": 1.0,
            "files": 1.0,
            "firewall": 1.0,
            "ports": 1.0,
            "crypto": 1.0,
            "admin": 1.0,
        },
    },
    "intrusion": {
        "scene_sync": "hybrid",
        "quality_mode": "auto",
        "ui_style": "full",
        "module_weights": {
            "nodes": 1.2,
            "files": 0.8,
            "firewall": 1.3,
            "ports": 1.25,
            "crypto": 0.9,
            "admin": 1.1,
        },
    },
    "data-heist": {
        "scene_sync": "bpm",
        "quality_mode": "auto",
        "ui_style": "minimal",
        "module_weights": {
            "nodes": 0.85,
            "files": 1.35,
            "firewall": 0.9,
            "ports": 0.95,
            "crypto": 1.2,
            "admin": 1.0,
        },
    },
}

# ---------------------------------------------------------------------------
# Mission phases
# ---------------------------------------------------------------------------
MISSION_PHASES: List[Dict[str, Any]] = [
    {
        "name": "RECON",
        "objective": "Map perimeter hosts and establish initial foothold",
        "operation": "RECON",
        "clearance": "L0",
        "net_state": "PASSIVE SWEEP",
    },
    {
        "name": "BREACH",
        "objective": "Exploit exposed services and collapse firewall segments",
        "operation": "BREACH",
        "clearance": "L1",
        "net_state": "FIREWALL COLLAPSE",
    },
    {
        "name": "EXFIL",
        "objective": "Secure data channel and stream priority assets",
        "operation": "EXFIL",
        "clearance": "L2",
        "net_state": "EXFIL PIPELINE",
    },
    {
        "name": "CLEANUP",
        "objective": "Purge traces, rotate identities, and disengage",
        "operation": "BACKDOOR",
        "clearance": "L3",
        "net_state": "TRACE WIPE",
    },
]


def apply_theme(name: str) -> str:
    """Apply a theme by name, updating the mutable CURRENT_STYLE globals."""
    global GREEN_BRIGHT, GREEN_DIM, GREEN_DARK, CURRENT_STYLE
    from cmd_audio.config import THEMES  # noqa: F811 – already module-level

    if name not in THEMES:
        name = "matrix"
    CURRENT_STYLE = THEME_STYLES[name]
    GREEN_BRIGHT = CURRENT_STYLE["bright"]
    GREEN_DIM = CURRENT_STYLE["dim"]
    GREEN_DARK = CURRENT_STYLE["dark"]
    return name


def set_bar_mode(use_unicode: bool) -> None:
    """Toggle Unicode vs ASCII bar characters."""
    global USE_UNICODE_BARS
    USE_UNICODE_BARS = bool(use_unicode)
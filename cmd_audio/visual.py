"""Visual rendering: network nodes, file transfer, firewall, crypto, ports, admin, processes, traffic, syslog, filesystem, ssh-brute, dns, db-dump, memory, spectrum, telemetry."""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cmd_audio.config as _cfg
from cmd_audio.effects import (
    build_banner_lines,
    build_spectrum_lines,
    meter_bar,
    panel_box,
)
from cmd_audio.utils import clamp, colorize_status, fit_text, random_ipv4


# ---------------------------------------------------------------------------
# Visual state (mutable, shared between frames)
# ---------------------------------------------------------------------------

@dataclass
class VisualState:
    node_rows: List[Tuple[str, str, bool]]
    file_rows: List[str]
    firewall_state: str
    crypto_algo: str
    port_rows: List[Tuple[str, str]]
    admin_rows: List[str]
    last_refresh: float
    # New hacking style state
    process_rows: List[Tuple[str, int, float, float, str]] = field(default_factory=list)
    syslog_lines: List[str] = field(default_factory=list)
    fs_entries: List[Tuple[str, str, str, str, str]] = field(default_factory=list)
    dns_results: List[str] = field(default_factory=list)
    db_rows: List[str] = field(default_factory=list)
    ssh_attempts: List[str] = field(default_factory=list)
    traffic_conns: List[str] = field(default_factory=list)
    mem_registers: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual module renderers
# ---------------------------------------------------------------------------

def render_network_nodes(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render Hacknet-style network node topology."""
    lines: List[str] = []
    node_count = min(5, max(3, height // 3))
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    rows = state.node_rows if state is not None and state.node_rows else []
    for i in range(node_count):
        if i < len(rows):
            node, port, breached = rows[i]
        else:
            node = random.choice(_cfg.NODE_TYPES)
            port = random.choice(_cfg.PORTS)
            breached = random.random() < activity
        status_text = "BREACHED" if breached else "SECURE"
        status = colorize_status(status_text, 0.95 if breached else 0.15)
        link_w = max(6, min(16, width // 6))
        link_fill = int(activity * link_w)
        connection = f"[{('=' * link_fill):<{link_w}}>]"
        line = f"{node:12} {port:4}  {status:8}  {connection}"
        lines.append(fit_text(line, width))
    lines.append(fit_text(f"Link load  {meter_bar(activity, max(8, width - 24))}", width))
    breach_ratio = sum(1 for _, _, b in rows[:node_count] if b) / max(1, node_count) if rows else 0.0
    lines.append(fit_text(f"Breach idx {meter_bar(breach_ratio, max(8, width - 24))}", width))
    if beat:
        lines.append(fit_text("[!] INTRUSION ALERT!", width))
    return lines[:height]


def render_file_transfer(
    level: float,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render file transfer progress bars."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    rows = state.file_rows if state is not None and state.file_rows else []
    file_count = min(3, max(1, height // 3))
    for i in range(file_count):
        file_name = rows[i] if i < len(rows) else random.choice(_cfg.FILE_OPS)
        bar_w = max(10, width - 30)
        line = f"{file_name:20} {meter_bar(activity, bar_w)}"
        lines.append(fit_text(line, width))
    return lines[:height]


def render_firewall_status(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render firewall breach status."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    wall_state = state.firewall_state if state is not None and state.firewall_state else random.choice(_cfg.FIREWALL_STATES)
    strength = int(activity * 100)

    header = f"FIREWALL: {wall_state} [{colorize_status(str(strength) + '%', activity)}]"
    lines.append(fit_text(header, width))

    bar_w = max(15, width - 10)
    lines.append(fit_text(f"BREACH {meter_bar(activity, bar_w)}", width))
    lines.append(fit_text(f"INTEGRITY {meter_bar(1.0 - activity, bar_w)}", width))

    if beat:
        lines.append(fit_text("[!] WALL DESTABILIZING", width))

    lines.append(fit_text(f"Port avail: {random.randint(2, 50)}", width))
    lines.append(fit_text(f"Exploits running: {max(1, int(activity * 6))}", width))

    return lines[:height]


def render_encryption_crack(
    level: float,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render encryption cracking progress."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    algo = state.crypto_algo if state is not None and state.crypto_algo else random.choice(_cfg.ENCRYPTION_ALGOS)
    lines.append(fit_text(f"Algorithm: {algo}", width))

    attempts = int(activity * 1000000)
    crack_pct = int(activity * 100)

    bar_w = max(15, width - 15)
    lines.append(fit_text(meter_bar(activity, bar_w), width))
    guess_ratio = clamp((activity * 0.92) + 0.06, 0.0, 1.0)
    lines.append(fit_text(f"Guess pass {meter_bar(guess_ratio, bar_w)}", width))
    lines.append(fit_text(f"Attempts: {attempts:,}", width))
    if crack_pct >= 100:
        lines.append(fit_text("[+] KEY RECOVERED!", width))

    return lines[:height]


def render_port_scan(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render port scan results."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    scanned = int(activity * 65535)
    lines.append(fit_text(f"NMAP SCAN: {scanned}/65535 ports", width))

    bar_w = max(12, width - 12)
    lines.append(fit_text(meter_bar(activity, bar_w), width))

    open_port_count = max(1, int(activity * 20))
    lines.append(fit_text(f"Open ports: {open_port_count}", width))
    lines.append(fit_text(f"Service map {meter_bar(open_port_count / 20.0, max(8, width - 16))}", width))

    rows = state.port_rows if state is not None and state.port_rows else []
    for i in range(min(3, height - 4)):
        if i < len(rows):
            port, service = rows[i]
        else:
            port = random.choice(_cfg.PORTS)
            service = random.choice(["ssh", "http", "ftp", "smtp", "vnc", "xrdp"])
        line = f"  {port:5} {service:8} open"
        lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text("[+] VULNERABILITY FOUND!", width))

    return lines[:height]


def render_admin_alerts(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render admin detection and alert system."""
    lines: List[str] = []

    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    alert_level = "CRITICAL" if beat else ("HIGH" if activity > 0.7 else "MEDIUM" if activity > 0.4 else "LOW")
    lines.append(fit_text(f"ALERT LEVEL: {colorize_status(alert_level, activity)}", width))
    lines.append(fit_text(f"Detect prob {meter_bar(activity, max(8, width - 16))}", width))

    rows = state.admin_rows if state is not None and state.admin_rows else []
    for i in range(min(4, height - 2)):
        if i < len(rows):
            alert = rows[i]
        else:
            port = random.choice(_cfg.PORTS)
            alert = random.choice(_cfg.ADMIN_NOTICES).format(port=port, count=random.randint(1, 100))
        lines.append(fit_text(alert[:width - 2], width))

    if beat:
        lines.append(fit_text("[!] ADMIN ONLINE!", width))

    return lines[:height]


# ---------------------------------------------------------------------------
# Process Monitor
# ---------------------------------------------------------------------------

def render_process_monitor(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a top/htop-style process monitor."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    total_procs = max(1, int(50 + activity * 150))
    running = max(1, int(activity * 8))
    sleeping = total_procs - running - 3
    zombie = 1 if beat else 0
    header = f"Tasks: {total_procs} total, {running} running, {sleeping} sleeping, {zombie} zombie"
    lines.append(fit_text(header, width))
    lines.append(fit_text(f"CPU: {int(activity * 100):3d}%  MEM: {int(activity * 8192):5d}/{16384}MB  SWAP: {int(activity * 512):4d}/{2048}MB", width))
    lines.append(fit_text(f"Load: {activity * 4.2:.2f}  {activity * 3.8:.2f}  {activity * 3.1:.2f}", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"CPU  {meter_bar(activity, bar_w)}", width))
    lines.append(fit_text(f"MEM  {meter_bar(clamp(activity * 0.6, 0, 1), bar_w)}", width))

    rows = state.process_rows if state is not None and state.process_rows else []
    proc_count = min(6, max(3, height - 6))
    for i in range(proc_count):
        if i < len(rows):
            name, pid, cpu, mem, st = rows[i]
        else:
            name = random.choice(_cfg.PROCESS_NAMES)
            pid = random.randint(100, 65000)
            cpu = round(random.random() * activity * 100, 1)
            mem = round(random.random() * activity * 8.0, 1)
            st = random.choice(_cfg.PROCESS_STATES)
        line = f"{pid:6d} {name:20s} {st:1s} {cpu:5.1f}% {mem:5.1f}%"
        if beat and i == 0:
            line += " <== SUSPICIOUS"
        lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text("[!] anomalous process detected -- investigating", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# Network Traffic Analyzer
# ---------------------------------------------------------------------------

def render_network_traffic(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a packet capture / traffic analysis view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    pkt_count = int(activity * 50000)
    byte_count = int(activity * 128 * 1024 * 1024)
    lines.append(fit_text(f"tcpdump: captured {pkt_count} packets ({byte_count // 1024}KB)", width))

    protocols = [
        ("TCP", 0.55 + random.random() * 0.2),
        ("UDP", 0.15 + random.random() * 0.1),
        ("ICMP", 0.05 + random.random() * 0.05),
        ("ARP", 0.03 + random.random() * 0.02),
        ("DNS", 0.10 + random.random() * 0.08),
        ("HTTP", 0.20 + random.random() * 0.15 * activity),
        ("HTTPS", 0.30 + random.random() * 0.20 * activity),
    ]
    bar_w = max(6, width - 22)
    for proto, ratio in protocols[:min(4, height - 5)]:
        r = clamp(ratio * activity, 0.0, 1.0)
        lines.append(fit_text(f"{proto:6s} {meter_bar(r, bar_w)} {int(r * 100):3d}%", width))

    lines.append(fit_text(f"Bandwidth: {activity * 940:.1f} Mbps  PPS: {int(activity * 12500)}", width))

    conns = state.traffic_conns if state is not None and state.traffic_conns else []
    conn_count = min(3, height - len(lines))
    for i in range(conn_count):
        if i < len(conns):
            lines.append(fit_text(conns[i], width))
        else:
            src = random_ipv4()
            dst = random_ipv4()
            sp = random.randint(1024, 65535)
            dp = random.choice([22, 80, 443, 3306, 5432, 8080, 8443])
            state_str = random.choice(["ESTABLISHED", "SYN_SENT", "TIME_WAIT", "CLOSE_WAIT", "FIN_WAIT1"])
            proto = random.choice(["TCP", "UDP"])
            lines.append(fit_text(f"  {src}:{sp} -> {dst}:{dp} {proto} {state_str}", width))

    if beat:
        lines.append(fit_text("[!] anomalous traffic spike detected", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# System Log Viewer
# ---------------------------------------------------------------------------

def render_system_log(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a streaming syslog / auth.log view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    rows = state.syslog_lines if state is not None and state.syslog_lines else []
    line_count = min(height, max(3, height))
    for i in range(line_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            sev = random.choice(_cfg.SYSLOG_SEVERITIES)
            if beat and i < 2:
                sev = random.choice(["EMERG", "ALERT", "CRIT"])
            elif activity > 0.7:
                sev = random.choice(["ERR", "WARN", "CRIT"])
            elif activity > 0.4:
                sev = random.choice(["WARN", "NOTICE", "INFO"])
            else:
                sev = random.choice(["INFO", "DEBUG", "NOTICE"])

            msg = random.choice(_cfg.SYSLOG_MESSAGES)
            msg = msg.format(
                ip=random_ipv4(),
                port=random.randint(1024, 65535),
                user=random.choice(_cfg.SSH_USERNAMES),
                pid=random.randint(100, 65000),
                count=random.randint(1, 9999),
            )
            ts = f"Jan  1 00:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            tag = random.choice(["sshd", "sudo", "kernel", "systemd", "nginx", "docker", "CRON", "polkitd"])
            line = f"{ts} target {tag}[{random.randint(100, 99999)}]: [{sev}] {msg}"

            # Colorize by severity
            if sev in ("EMERG", "ALERT", "CRIT"):
                line = f"{_cfg.STATUS_CRIT}{fit_text(line, width)}{_cfg.RESET}"
            elif sev == "ERR":
                line = f"{_cfg.STATUS_WARN}{fit_text(line, width)}{_cfg.RESET}"
            else:
                line = fit_text(line, width)
            lines.append(line)

    return lines[:height]


# ---------------------------------------------------------------------------
# Filesystem Browser
# ---------------------------------------------------------------------------

def render_filesystem(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a fake filesystem traversal (ls -la style)."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    lines.append(fit_text(f"root@target:/# find / -maxdepth 2 -ls 2>/dev/null", width))
    lines.append(fit_text(f"scanning... {int(activity * 100)}% complete", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"SCAN  {meter_bar(activity, bar_w)}", width))

    rows = state.fs_entries if state is not None and state.fs_entries else []
    entry_count = min(5, max(2, height - 4))
    for i in range(entry_count):
        if i < len(rows):
            path, perms, owner, group, size = rows[i]
        else:
            entry = random.choice(_cfg.FILESYSTEM_ENTRIES)
            path, perms, owner, group, size = entry
        line = f"{perms} {owner:8s} {group:8s} {size:>10s} {path}"
        # Highlight sensitive files
        if any(k in path for k in ("shadow", "id_rsa", "backdoor", ".ssh", "config.php", "database.db")):
            line = f"{_cfg.STATUS_CRIT}{fit_text(line, width)}{_cfg.RESET}"
        else:
            line = fit_text(line, width)
        lines.append(line)

    if beat:
        lines.append(fit_text("[+] sensitive file located -- extracting", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# SSH Brute Force
# ---------------------------------------------------------------------------

def render_ssh_bruteforce(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render SSH brute-force login attempts."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    attempts = int(activity * 50000)
    successes = max(0, int(activity * activity * 10))
    lines.append(fit_text(f"hydra: {attempts} attempts  {successes} successful", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"BRUTE {meter_bar(activity, bar_w)}", width))

    rows = state.ssh_attempts if state is not None and state.ssh_attempts else []
    attempt_count = min(5, max(3, height - 3))
    for i in range(attempt_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            user = random.choice(_cfg.SSH_USERNAMES)
            passwd = random.choice(_cfg.SSH_PASSWORDS)
            ip = random_ipv4()
            port = random.randint(1024, 65535)
            # Success on beat with high activity
            if beat and i == 0 and activity > 0.8:
                status = colorize_status("[+] ACCESS GRANTED", 0.95)
                line = f"  {ip}:{port} {user}:{passwd} {status}"
            else:
                status = colorize_status("[-] FAILED", 0.3)
                line = f"  {ip}:{port} {user}:{passwd} {status}"
            lines.append(fit_text(line, width))

    if beat and activity > 0.8:
        lines.append(fit_text("[!] shell access acquired!", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# DNS Enumeration
# ---------------------------------------------------------------------------

def render_dns_enum(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render DNS enumeration / subdomain discovery."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    domain = random.choice(_cfg.DNS_DOMAINS)
    discovered = max(1, int(activity * len(_cfg.DNS_SUBDOMAINS)))
    lines.append(fit_text(f"dnsenum --enum {domain}  [{discovered} subdomains found]", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"ENUM  {meter_bar(activity, bar_w)}", width))

    rows = state.dns_results if state is not None and state.dns_results else []
    result_count = min(5, max(3, height - 3))
    for i in range(result_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            sub = random.choice(_cfg.DNS_SUBDOMAINS)
            rec_type = random.choice(_cfg.DNS_RECORD_TYPES)
            if rec_type in ("A", "AAAA"):
                value = random_ipv4()
            elif rec_type == "MX":
                value = f"mail.{domain}"
            elif rec_type == "CNAME":
                value = f"lb.{domain}"
            elif rec_type == "TXT":
                value = random.choice(["v=spf1 include:_spf.google.com ~all", "\"google-site-verification=abc123\""])
            else:
                value = f"ns1.{domain}"
            fqdn = f"{sub}.{domain}"
            line = f"  {fqdn:40s} {rec_type:6s} {value}"
            if beat and i == 0:
                line = f"[+] {fqdn:38s} {rec_type:6s} {value}"
            lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text("[!] zone transfer accepted -- dumping records", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# Database Dump
# ---------------------------------------------------------------------------

def render_db_dump(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render SQL database dump / credential extraction."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    table = random.choice(_cfg.DB_TABLES)
    rows_dumped = max(1, int(activity * 10000))
    lines.append(fit_text(f"SELECT * FROM {table} LIMIT {rows_dumped};", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"DUMP  {meter_bar(activity, bar_w)}", width))

    # Table header
    cols = random.sample(_cfg.DB_COLUMNS, k=min(4, width // 16))
    header = " | ".join(c[:12].ljust(12) for c in cols)
    lines.append(fit_text(header[:width - 1], width))
    sep = "-+-".join("-" * 12 for _ in cols)
    lines.append(fit_text(sep[:width - 1], width))

    rows = state.db_rows if state is not None and state.db_rows else []
    row_count = min(4, max(2, height - 5))
    for i in range(row_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            vals = []
            for c in cols:
                if "password" in c or "secret" in c or "key" in c or "token" in c:
                    if beat and activity > 0.7:
                        vals.append("REDACTED!!!")
                    else:
                        vals.append("*" * 10)
                elif "id" in c:
                    vals.append(str(random.randint(1, 9999)))
                elif "email" in c:
                    vals.append(f"user{random.randint(1, 999)}@corp.net")
                elif "ip" in c:
                    vals.append(random_ipv4()[:15])
                elif "date" in c or "at" in c:
                    vals.append(f"2026-0{random.randint(1, 9)}-{random.randint(1, 28):02d}")
                elif "admin" in c or "active" in c:
                    vals.append(str(random.choice([0, 1])))
                elif "amount" in c or "balance" in c:
                    vals.append(f"{random.randint(0, 99999):.2f}")
                else:
                    vals.append(f"val_{random.randint(1, 999)}")
            line = " | ".join(v[:12].ljust(12) for v in vals)
            lines.append(fit_text(line[:width - 1], width))

    if beat and activity > 0.8:
        lines.append(fit_text("[+] credentials extracted -- admin access", width))
    return lines[:height]


# ---------------------------------------------------------------------------
# Memory / Register Analysis
# ---------------------------------------------------------------------------

def render_memory_analysis(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render register values, stack traces, and disassembly."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    lines.append(fit_text("gdb$ info registers", width))

    rows = state.mem_registers if state is not None and state.mem_registers else []
    reg_count = min(4, max(2, height - 5))
    for i in range(reg_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            reg = random.choice(_cfg.REGISTER_NAMES)
            val = random.randint(0, 0xFFFFFFFFFFFFFFFF)
            if beat and i == 0:
                line = f"  {reg:8s} 0x{val:016x}  <-- BREAKPOINT HIT"
                line = f"{_cfg.STATUS_CRIT}{fit_text(line, width)}{_cfg.RESET}"
            else:
                line = f"  {reg:8s} 0x{val:016x}"
                line = fit_text(line, width)
            lines.append(line)

    # Disassembly snippet
    lines.append(fit_text("gdb$ x/4i $rip", width))
    addr = random.randint(0x400000, 0x7FFFFFFF)
    asm_count = min(3, max(1, height - len(lines)))
    for i in range(asm_count):
        if beat and i == 0:
            mnemonic = "syscall"
        else:
            mnemonic = random.choice(_cfg.ASSEMBLY_MNEMONICS)
        operand1 = f"0x{random.randint(0, 0xFFFFFFFF):x}"
        operand2 = random.choice([
            f"0x{random.randint(0, 0xFF):x}",
            f"%{random.choice(['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rsp', 'rbp'])}",
            f"0x{random.randint(0, 0xFFFF):x}(%{random.choice(['rbp', 'rsp'])})",
        ])
        line = f"  0x{addr + i * 4:08x}: {mnemonic:8s} {operand1}, {operand2}"
        lines.append(fit_text(line, width))

    analysis_pct = int(activity * 100)
    lines.append(fit_text(f"Analysis: {analysis_pct}%  Stack depth: {max(1, int(activity * 32))}", width))
    bar_w = max(8, width - 18)
    lines.append(fit_text(f"ANALY {meter_bar(activity, bar_w)}", width))

    if beat:
        lines.append(fit_text("[!] buffer overflow pattern matched at 0x{:08x}".format(addr), width))
    return lines[:height]


# ---------------------------------------------------------------------------
# Shell feed
# ---------------------------------------------------------------------------

def generate_shell_feed(level: float, beat: bool, terminal_mode: str) -> List[str]:
    host = random.choice(_cfg.TARGETS)
    ip = random_ipv4()
    port = random.choice(_cfg.PORTS)
    profile = _cfg.TERMINAL_PROFILES.get(terminal_mode) or _cfg.TERMINAL_PROFILES["netrunner"]
    prompt = str(profile["prompt"])
    commands = [str(x) for x in profile["commands"]]
    statuses = [str(x) for x in profile["status"]]
    cmd = random.choice(commands).format(host=host)
    progress = int(level * 100)
    retry_count = random.randint(2, 14)

    lines = [
        f"{prompt} {cmd}",
        f"[*] routing via {ip}:{port}",
        f"[*] entropy-scan {host}  confidence={progress:02d}%",
    ]
    state_line = random.choice(statuses).format(host=host, count=retry_count)
    lines.append(state_line)
    if beat:
        lines.append("[+] beat lock acquired -> switching payload profile")

    return lines


def build_shell_feed(shell_lines: List[str], width: int, max_lines: int) -> List[str]:
    if max_lines <= 0:
        return []
    return [fit_text(line, width) for line in shell_lines[:max_lines]]


# ---------------------------------------------------------------------------
# Visual mode renderers
# ---------------------------------------------------------------------------

def render_visual_mode(
    mode: str,
    level: float,
    beat: bool,
    bands: List[float],
    history: List[float],
    shell_lines: List[str],
    width: int,
    height: int,
    quality_scale: float,
) -> List[str]:
    """Render current Hacknet visual mode."""
    if mode == "nodes":
        return render_network_nodes(level, beat, width, height)
    elif mode == "files":
        return render_file_transfer(level, width, height)
    elif mode == "firewall":
        return render_firewall_status(level, beat, width, height)
    elif mode == "crypto":
        return render_encryption_crack(level, width, height)
    elif mode == "ports":
        return render_port_scan(level, beat, width, height)
    elif mode == "admin":
        return render_admin_alerts(level, beat, width, height)
    elif mode == "processes":
        return render_process_monitor(level, beat, width, height)
    elif mode == "traffic":
        return render_network_traffic(level, beat, width, height)
    elif mode == "syslog":
        return render_system_log(level, beat, width, height)
    elif mode == "filesystem":
        return render_filesystem(level, beat, width, height)
    elif mode == "ssh-brute":
        return render_ssh_bruteforce(level, beat, width, height)
    elif mode == "dns":
        return render_dns_enum(level, beat, width, height)
    elif mode == "db-dump":
        return render_db_dump(level, beat, width, height)
    elif mode == "memory":
        return render_memory_analysis(level, beat, width, height)
    else:
        return build_spectrum_lines(bands, width, height, history, shell_lines, quality_scale)


def render_paneled_visuals(
    level: float,
    beat: bool,
    bands: List[float],
    history: List[float],
    shell_lines: List[str],
    width: int,
    height: int,
    quality_scale: float,
    module_levels: Dict[str, float],
    state: Optional[VisualState],
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Render separate Hacknet feeds sized for embedding in a composed center panel."""
    del bands, history, shell_lines, quality_scale
    panel_w = max(10, width)
    panel_h = max(2, height)

    nodes = render_network_nodes(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("nodes", level))
    firewall = render_firewall_status(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("firewall", level))
    ports = render_port_scan(level, beat, panel_w, panel_h, state=state, module_level=module_levels.get("ports", level))
    crypto = render_encryption_crack(level, panel_w, panel_h, state=state, module_level=module_levels.get("crypto", level))

    return nodes, firewall, ports, crypto


def compose_center_panel(
    center_w: int,
    center_h: int,
    nodes: List[str],
    firewall: List[str],
    ports: List[str],
    crypto: List[str],
) -> List[str]:
    """Compose four separated hacking modules into a single center panel body."""
    if center_h <= 0:
        return []

    out: List[str] = []
    sections = [
        ("nodes", nodes),
        ("firewall", firewall),
        ("ports", ports),
        ("crypto", crypto),
    ]
    sec_h = max(2, center_h // len(sections))

    for idx, (name, lines) in enumerate(sections):
        label = f"< {name.upper()} >"
        edge_w = max(1, (center_w - len(label)) // 2)
        header_raw = ("-" * edge_w) + label + ("-" * max(1, center_w - edge_w - len(label)))
        out.append(f"{_cfg.GREEN_DIM}{fit_text(header_raw, center_w)}{_cfg.RESET}")

        usable = max(1, sec_h - 2)
        used = 0
        for line in lines[:usable]:
            out.append(fit_text(line, center_w))
            used += 1
        fill_line = fit_text("", center_w)
        while used < usable:
            out.append(fill_line)
            used += 1
        if idx < len(sections) - 1:
            sep_raw = ":" * max(1, center_w)
            out.append(f"{_cfg.GREEN_DARK}{fit_text(sep_raw, center_w)}{_cfg.RESET}")

    return out[:center_h]


# ---------------------------------------------------------------------------
# Visual state refresh
# ---------------------------------------------------------------------------

def refresh_visual_state(
    state: VisualState,
    module_levels: Dict[str, float],
    beat: bool,
    flux: float,
    t: float,
) -> None:
    churn = 0.10 + (0.35 * module_levels.get("nodes", 0.0)) + (0.25 * flux)
    if (t - state.last_refresh) < 0.22 and not beat:
        return

    target_nodes = 5
    if not state.node_rows:
        state.node_rows = [(random.choice(_cfg.NODE_TYPES), random.choice(_cfg.PORTS), random.random() < module_levels.get("nodes", 0.0)) for _ in range(target_nodes)]
    else:
        next_rows: List[Tuple[str, str, bool]] = []
        for node, port, breached in state.node_rows[:target_nodes]:
            if random.random() < churn:
                node = random.choice(_cfg.NODE_TYPES)
            if random.random() < churn:
                port = random.choice(_cfg.PORTS)
            if random.random() < (0.08 + (0.60 * module_levels.get("nodes", 0.0))):
                breached = not breached
            next_rows.append((node, port, breached))
        while len(next_rows) < target_nodes:
            next_rows.append((random.choice(_cfg.NODE_TYPES), random.choice(_cfg.PORTS), random.random() < module_levels.get("nodes", 0.0)))
        state.node_rows = next_rows

    if (not state.file_rows) or random.random() < (0.15 + (0.35 * module_levels.get("files", 0.0))):
        state.file_rows = random.sample(_cfg.FILE_OPS, k=min(4, len(_cfg.FILE_OPS)))

    if random.random() < (0.18 + (0.55 * module_levels.get("firewall", 0.0))):
        if module_levels.get("firewall", 0.0) > 0.7:
            state.firewall_state = random.choice(["WALL_BREACH", "ICE_DETECTED", "FIREWALL_DOWN"])
        else:
            state.firewall_state = random.choice(_cfg.FIREWALL_STATES)

    if random.random() < (0.15 + (0.55 * module_levels.get("crypto", 0.0))):
        state.crypto_algo = random.choice(_cfg.ENCRYPTION_ALGOS)

    if (not state.port_rows) or random.random() < (0.14 + (0.45 * module_levels.get("ports", 0.0))):
        services = ["ssh", "http", "ftp", "smtp", "vnc", "xrdp"]
        state.port_rows = [(random.choice(_cfg.PORTS), random.choice(services)) for _ in range(4)]

    if (not state.admin_rows) or random.random() < (0.12 + (0.40 * module_levels.get("admin", 0.0))):
        state.admin_rows = [
            random.choice(_cfg.ADMIN_NOTICES).format(port=random.choice(_cfg.PORTS), count=random.randint(1, 100))
            for _ in range(4)
        ]

    # --- New hacking style state refresh ---

    if random.random() < (0.15 + (0.45 * module_levels.get("processes", 0.0))):
        state.process_rows = [
            (random.choice(_cfg.PROCESS_NAMES), random.randint(100, 65000),
             round(random.random() * 100, 1), round(random.random() * 8.0, 1),
             random.choice(_cfg.PROCESS_STATES))
            for _ in range(6)
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("syslog", 0.0))):
        state.syslog_lines = []

    if random.random() < (0.14 + (0.40 * module_levels.get("filesystem", 0.0))):
        state.fs_entries = [random.choice(_cfg.FILESYSTEM_ENTRIES) for _ in range(6)]

    if random.random() < (0.13 + (0.40 * module_levels.get("dns", 0.0))):
        state.dns_results = []

    if random.random() < (0.14 + (0.40 * module_levels.get("db-dump", 0.0))):
        state.db_rows = []

    if random.random() < (0.12 + (0.40 * module_levels.get("ssh-brute", 0.0))):
        state.ssh_attempts = []

    if random.random() < (0.15 + (0.40 * module_levels.get("traffic", 0.0))):
        state.traffic_conns = [
            f"  {random_ipv4()}:{random.randint(1024, 65535)} -> {random_ipv4()}:{random.choice([22, 80, 443, 3306])} {random.choice(['TCP', 'UDP'])} {random.choice(['ESTABLISHED', 'SYN_SENT', 'TIME_WAIT'])}"
            for _ in range(3)
        ]

    if random.random() < (0.13 + (0.40 * module_levels.get("memory", 0.0))):
        state.mem_registers = [
            f"  {random.choice(_cfg.REGISTER_NAMES):8s} 0x{random.randint(0, 0xFFFFFFFFFFFFFFFF):016x}"
            for _ in range(6)
        ]

    state.last_refresh = t


# ---------------------------------------------------------------------------
# Telemetry lines
# ---------------------------------------------------------------------------

def build_telemetry_lines(
    level: float,
    t: float,
    duration: float,
    width: int,
    pulse: int,
    speed_factor: float,
    sensitivity: float,
    theme_name: str,
    terminal_mode: str,
    switch_min: float,
    switch_max: float,
    daemon: str,
    clearance: str,
    open_ports: int,
    trace_hops: int,
    packet: int,
    flux: float,
    mission_phase: str,
    mission_objective: str,
    defender_state: str,
    keys_line: str,
) -> List[str]:
    progress = clamp(t / duration if duration > 0 else 0.0, 0.0, 1.0)
    prog_w = max(8, width - 14)
    mini_w = max(8, width - 18)
    status = "LOCKED" if pulse > 0 else "TRACK"
    mood = "PEAK" if level > 0.75 else "FLOW" if level > 0.45 else "LOW"
    entropy = 3.2 + (level * 4.7)
    trace_ratio = clamp(trace_hops / 12.0, 0.0, 1.0)

    return [
        f"time     {t:7.2f}s / {duration:7.2f}s",
        f"level    {int(level * 100):3d}%   mood {mood}",
        f"status   {status}",
        f"clear    {clearance}",
        f"mission  {mission_phase}",
        f"defense  {defender_state}",
        f"daemon   {daemon}",
        f"ports    {open_ports:2d} open",
        f"trace    {trace_hops:2d} hops",
        f"speed    x{speed_factor:0.2f}",
        f"level m  {meter_bar(level, mini_w)}",
        f"flux m   {meter_bar(flux, mini_w)}",
        f"trace m  {meter_bar(trace_ratio, mini_w)}",
        f"sens     x{sensitivity:0.2f}",
        f"theme    {theme_name}",
        f"term     {terminal_mode}",
        f"switch   {switch_min:0.1f}-{switch_max:0.1f}s",
        f"entropy  {entropy:4.2f} bits",
        f"packet   {packet:5d} bytes",
        fit_text(f"obj      {mission_objective}", width),
        "",
        f"progress {meter_bar(progress, prog_w)}",
        "",
        keys_line,
    ]
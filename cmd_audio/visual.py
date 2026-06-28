"""Visual rendering: network nodes, file transfer, firewall, crypto, ports, admin, processes, traffic, syslog, filesystem, ssh-brute, dns, db-dump, memory, spectrum, telemetry + 18 new modules."""

from __future__ import annotations

import math
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
    # 18 new modules state
    buffer_overflow_stack: List[str] = field(default_factory=list)
    geo_trace_hops: List[str] = field(default_factory=list)
    vhs_lines: List[str] = field(default_factory=list)
    radar_blips: List[Tuple[float, float, str, float]] = field(default_factory=list)  # angle, distance, type, life
    particle_stars: List[Tuple[float, float, float, float, str, float]] = field(default_factory=list)  # x, y, vx, vy, ch, life
    payload_lines: List[str] = field(default_factory=list)
    sqli_lines: List[str] = field(default_factory=list)
    vpn_layers: List[str] = field(default_factory=list)
    k8s_pods: List[Tuple[str, str, str, str]] = field(default_factory=list)  # name, image, phase, ip
    iot_devices: List[Tuple[str, str, str, bool]] = field(default_factory=list)  # type, ip, fw, infected
    packet_lines: List[str] = field(default_factory=list)
    stego_lines: List[str] = field(default_factory=list)
    crack_rows: List[Tuple[str, str, int, int, float]] = field(default_factory=list)  # algo, hash, cracked, total, rate
    aurora_buf: List[str] = field(default_factory=list)
    bios_lines: List[str] = field(default_factory=list)
    morse_lines: List[str] = field(default_factory=list)
    whois_data: List[str] = field(default_factory=list)
    cert_data: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual module renderers (existing ones unchanged above)
# ---------------------------------------------------------------------------
# [existing render functions remain in the file, they are already defined above]
# We add all new modules below


# =========================================================================
# 1. BUFFER OVERFLOW
# =========================================================================

def render_buffer_overflow(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render an ASCII stack diagram showing buffer overflow exploitation."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    exploit = random.choice(_cfg.EXPLOIT_TYPES) if not beat or activity < 0.5 else "SEH-overwrite"
    lines.append(fit_text(f"[*] {exploit.upper()} -- building payload", width))
    lines.append(fit_text(f"PAYLOAD {meter_bar(activity, bar_w)}", width))

    # Stack diagram
    stack_h = min(height - 4, 8)
    rows_used = 0
    stack_diagram = state.buffer_overflow_stack if state and state.buffer_overflow_stack else []
    for i in range(stack_h):
        if i < len(stack_diagram):
            lines.append(fit_text(stack_diagram[i], width))
        else:
            row_type = i % 4
            if row_type == 0:
                nop_len = int(activity * 64)
                nop_sled = f"    NOP SLED [{_cfg.GREEN_DIM}{'\\x90' * min(nop_len, width // 4 - 12)}{_cfg.RESET}]"
                lines.append(fit_text(nop_sled, width))
            elif row_type == 1:
                lines.append(fit_text(f"    buf[{i}] = 0x{random.randint(0, 0xFFFFFFFF):08x}  <-- overflow", width))
            elif row_type == 2:
                saved_ebp = f"0x{random.randint(0x7FFFFFF0, 0x7FFFFFFF):08x}"
                marker = " <<< OVERWRITTEN!" if beat else ""
                lines.append(fit_text(f"    Saved EBP = {saved_ebp}{marker}", width))
            elif row_type == 3:
                ret_addr = f"0x{random.randint(0x08040000, 0x0804FFFF):08x}"
                marker = f" {_cfg.STATUS_CRIT}<<< SHELLCODE!{_cfg.RESET}" if beat else ""
                lines.append(fit_text(f"    RET ADDR = {ret_addr}{marker}", width))
            rows_used += 1

    if beat:
        payload = random.choice(_cfg.SHELLCODE_PAYLOADS)
        lines.append(fit_text(f"[+] shellcode injected: {payload}", width))
        lines.append(fit_text(f"[!] EIP overwritten -- execution hijacked", width))

    return lines[:height]


# =========================================================================
# 2. GEO TRACE
# =========================================================================

def render_geo_trace(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a geographic IP traceroute with mini ASCII world map."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    hop_count = max(2, min(8, height - 4))
    hops = state.geo_trace_hops if state and state.geo_trace_hops else []

    lines.append(fit_text("traceroute to target.corp (10.0.0.1)", width))
    lines.append(fit_text(f"hops: {hop_count}  progress {meter_bar(activity, max(8, width - 24))}", width))

    # Mini ASCII world map
    if width > 30 and height > hop_count + 3:
        map_w = min(25, width - 10)
        map_str = _build_ascii_worldmap(activity, map_w)
        lines.append(fit_text(f"  {map_str}", width))

    for i in range(hop_count):
        if i < len(hops):
            lines.append(fit_text(hops[i], width))
        else:
            if i == 0:
                city = random.choice(_cfg.CITIES)
                lines.append(fit_text(f"  {1:2d}  {city[0]:12s} ({city[1]:.2f}, {city[2]:.2f})  {random.choice(_cfg.ISP_NAMES):20s}  {random.choice(_cfg.AS_NUMBERS):8s}  {random.randint(1, 30):2d}ms", width))
            elif i == hop_count - 1:
                lines.append(fit_text(f"  {i+1:2d}  *** TARGET ***                           {random.choice(_cfg.AS_NUMBERS):8s}  {random.randint(50, 200):3d}ms", width))
            else:
                city = random.choice(_cfg.CITIES)
                rtt = random.randint(5, 80) + int(activity * 40)
                loss = int(random.random() * activity * 10)
                marker = " [!]" if beat and i == hop_count // 2 else ""
                lines.append(fit_text(f"  {i+1:2d}  {city[0]:12s} ({city[1]:.2f}, {city[2]:.2f})  {random.choice(_cfg.ISP_NAMES):20s}  {random.choice(_cfg.AS_NUMBERS):8s}  {rtt:3d}ms loss={loss}%{marker}", width))

    if beat:
        lines.append(fit_text("[!] route anomaly detected -- packet loss spike", width))

    return lines[:height]


def _build_ascii_worldmap(activity: float, map_w: int) -> str:
    """Build a simple ASCII world map representation dot at activity position."""
    map_template = (
        "                                                          \n"
        "        .---.    .---.        .---.                       \n"
        "       /     \\  /     \\      /     \\   AMER             \n"
        "      /       \\/       \\    /       \\                    \n"
        "     /  AMER   \\  ATL  /   /  EURO   \\                   \n"
        "    /           \\     /   /           \\                  \n"
        "   '-------------'---'   '-------------'                  \n"
        "                     .---.                                \n"
        "                    /     \\     ASIA                      \n"
        "          AFRICA   /       \\                             \n"
        "                  /         \\                            \n"
        "                 /           \\                           \n"
        "                '-------------'                           \n"
        "                         .---. -- AUS                     \n"
        "                        /     \\                          \n"
        "                       '-----'                            \n"
        "  ANT                                                      "
    )
    lines = map_template.strip().split('\n')
    if len(lines) == 0:
        return ""
    idx = int(activity * (len(lines) - 1))
    line = lines[idx]
    if map_w < len(line):
        line = line[:map_w]
    return line


# =========================================================================
# 3. VHS GLITCH
# =========================================================================

def render_vhs_glitch(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a VHS tracking error simulation."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    lines.append(fit_text(f"VHS TRACKING: {random.choice(_cfg.VHS_TRACKING_MODES)}  TAPE: {random.choice(_cfg.VHS_TAPE_LABELS)}", width))
    lines.append(fit_text(f"TIMEBASE {meter_bar(activity, bar_w)}", width))

    # Timestamp burn-in
    ts = random.choice(_cfg.VHS_TIMESTAMPS) if not beat else f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}:{random.randint(0, 29):02d}"
    lines.append(fit_text(f"  {_cfg.GREEN_DIM}[{ts}]{_cfg.RESET}", width))

    # Scan line distortion
    rows_remaining = height - len(lines)
    for i in range(rows_remaining):
        if activity < 0.3:
            # Normal-ish playback
            ch = random.choice([" ", ".", ":", "~", "-", "="])
            noise_len = int(width * 0.1)
            left = " " * random.randint(0, width // 4)
            middle = ch * noise_len
            right = " " * (width - len(left) - noise_len)
            line_str = left + middle + right
        elif activity < 0.6:
            # Tracking lines
            offset = random.randint(0, width // 2)
            line_str = " " * offset + "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁" + " " * (width - offset - 15)
        elif activity < 0.9:
            # Heavy distortion
            if beat and i == rows_remaining // 2:
                line_str = "▂▃▄▅▆▇██▇▆▅▄▃▂" * (width // 13 + 1)
            else:
                line_str = "".join(random.choice(["█", "▓", "▒", "░", "▄", "▀", " "]) for _ in range(width))
        else:
            # Extreme glitch / signal loss
            if beat:
                line_str = ("!" * width) if i % 2 == 0 else ("#" * width)
            else:
                gray = chr(0x2591 + random.randint(0, 2)) if random.random() < 0.7 else " "
                line_str = gray * width

        # Color shift
        if beat and i == rows_remaining // 3:
            line_str = f"{_cfg.STATUS_CRIT}{line_str[:width]}{_cfg.RESET}"
        elif activity > 0.5 and i % 3 == 0:
            line_str = f"{_cfg.GREEN_DIM}{line_str[:width]}{_cfg.RESET}"
        else:
            line_str = fit_text(line_str, width)

        lines.append(line_str)

    return lines[:height]


# =========================================================================
# 4. RADAR SWEEP
# =========================================================================

def render_radar_sweep(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a circular radar sweep visualization."""
    from cmd_audio.utils import clamp as _clamp

    lines: List[str] = []
    activity = _clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    # Radar circle
    rad = min(width // 3 - 1, height // 2 - 2, 10)
    rad = max(3, rad)
    cx = width // 2
    cy = (height - 2) // 2
    sweep_angle = ((state.last_refresh * 90) % 360 if state else 0)

    grid: List[List[str]] = [[" "] * width for _ in range(height - 2)]

    # Draw crosshairs
    for y in range(min(height - 2, cy * 2)):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if abs(dist - rad) < 0.8:
                grid[y][x] = _cfg.GREEN_DIM + "." + _cfg.RESET
            if abs(dx) < 0.8 and dy > -rad and dy < rad:
                grid[y][x] = _cfg.GREEN_DIM + "|" + _cfg.RESET
            if abs(dy) < 0.8 and dx > -rad and dx < rad:
                grid[y][x] = _cfg.GREEN_DIM + "-" + _cfg.RESET
            # Sweep line
            angle_rad = math.radians(sweep_angle - 90)
            if abs(math.atan2(dy, dx) - angle_rad) < 0.15 and dist < rad:
                grid[y][x] = _cfg.GREEN_BRIGHT + "+" + _cfg.RESET

    # Blips
    blips = state.radar_blips if state else []
    for angle, dist, blip_type, life in blips:
        if life <= 0:
            continue
        bx = int(cx + dist * rad * math.cos(math.radians(angle - 90)))
        by = int(cy + dist * rad * math.sin(math.radians(angle - 90)))
        if 0 <= bx < width and 0 <= by < min(height - 2, cy * 2):
            ch = "●"
            if blip_type == "HOSTILE":
                ch = f"{_cfg.STATUS_CRIT}●{_cfg.RESET}"
            elif blip_type == "FRIENDLY":
                ch = f"{_cfg.STATUS_OK}●{_cfg.RESET}"
            elif blip_type == "UNKNOWN":
                ch = f"{_cfg.STATUS_WARN}?{_cfg.RESET}"
            grid[by][bx] = ch

    for row in grid:
        lines.append("".join(row))

    lines.append(fit_text(f"SWEEP {meter_bar(activity, bar_w)}  BLIPS: {len(blips)}", width))

    if beat:
        lines.append(fit_text("[!] HOSTILE CONTACT -- LOCKING TARGET", width))

    return lines[:height]


# =========================================================================
# 5. PARTICLE STORM  [FIXED: no double-width Unicode chars to prevent UI breakage]
# =========================================================================

def render_particle_storm(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render an ASCII particle system / fireworks reacting to audio.
    Uses only single-width ASCII characters to avoid terminal alignment issues."""
    from cmd_audio.utils import clamp as _clamp

    lines: List[str] = []
    activity = _clamp(module_level if module_level is not None else level, 0.0, 1.0)

    grid: List[List[str]] = [[" "] * width for _ in range(height)]

    particles = state.particle_stars if state else []
    new_particles: List[Tuple[float, float, float, float, str, float]] = []

    for x, y, vx, vy, ch, life in particles:
        if life > 0:
            nx = x + vx
            ny = y + vy
            if 0 <= nx < width and 0 <= ny < height:
                grid[int(ny)][int(nx)] = ch
                new_particles.append((nx, ny, vx, vy * 0.99 + 0.05, ch, life - 1))

    # Spawn new particles on beat or high activity
    spawn_rate = int(activity * 5) + (3 if beat else 0)
    for _ in range(spawn_rate):
        px = random.random() * width
        py = random.random() * height * 0.5
        pvx = (random.random() - 0.5) * 2
        pvy = random.random() * 2 + 1 if beat else random.random() * 1.5
        # Use only single-width ASCII chars — no double-width Unicode to avoid UI breakage
        pch = random.choice("*.:+#%@oO")
        plife = 10 + int(activity * 20) + (10 if beat else 0)
        new_particles.append((px, py, pvx, pvy, pch, plife))

    if state:
        state.particle_stars = new_particles[:100]  # cap at 100

    # Use fit_text on each row to ensure consistent width despite variable-width chars
    for row in grid:
        lines.append(fit_text("".join(row), width))

    return lines[:height]


# =========================================================================
# 6. PAYLOAD BUILDER
# =========================================================================

def render_payload_builder(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a Metasploit-style payload generator."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    payload = random.choice(_cfg.PAYLOAD_TYPES)
    encoder = random.choice(_cfg.PAYLOAD_ENCODERS)
    stage = random.choice(_cfg.PAYLOAD_STAGES)

    lines.append(fit_text(f"msfvenom -p {payload}", width))
    lines.append(fit_text(f"LHOST=192.168.1.{random.randint(2, 254)}  LPORT={random.randint(4444, 9999)}", width))
    lines.append(fit_text(f"Encoder: {encoder}  Stage: {stage}", width))
    lines.append(fit_text(f"BUILD {meter_bar(activity, bar_w)}", width))

    # Hex output simulation
    payload_size = int(activity * 1024)
    hex_lines = state.payload_lines if state and state.payload_lines else []
    hex_count = min(height - 5, 6)
    for i in range(hex_count):
        if i < len(hex_lines):
            lines.append(fit_text(hex_lines[i], width))
        else:
            addr = 0x08040000 + i * 16
            hex_bytes = " ".join(f"{random.randint(0, 255):02x}" for _ in range(16))
            ascii_repr = "".join(chr(random.randint(32, 126)) if random.random() < 0.7 else "." for _ in range(16))
            line = f"  0x{addr:08x}: {hex_bytes}  |{ascii_repr}|"
            if beat and i == 0:
                line = f"{_cfg.STATUS_CRIT}{line}{_cfg.RESET}"
            lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text(f"[+] payload compiled: {payload_size} bytes", width))

    return lines[:height]


# =========================================================================
# 7. SQL INJECTION
# =========================================================================

def render_sql_injection(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render SQL injection attempts and results."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    tech = random.choice(_cfg.SQLI_TECHNIQUES)
    db_ver = random.choice(_cfg.DB_VERSIONS)

    lines.append(fit_text(f"sqlmap -u http://target.corp/page?id=1 --technique={tech}", width))
    lines.append(fit_text(f"DB: {db_ver}  [tables: {random.randint(10, 100)}]", width))
    lines.append(fit_text(f"INJECT {meter_bar(activity, bar_w)}", width))

    payloads = state.sqli_lines if state and state.sqli_lines else []
    payload_count = min(height - 4, 6)
    for i in range(payload_count):
        if i < len(payloads):
            lines.append(fit_text(payloads[i], width))
        else:
            if random.random() < 0.3:
                # Successful injection
                line = f"  [+] {random.choice(['admin', 'user', 'root'])}:{random.choice(['password', 'secret', '123456'])}:{random.choice(['admin', 'user', 'guest'])}"
                line = f"{_cfg.STATUS_OK}{fit_text(line, width)}{_cfg.RESET}"
            else:
                sqli = random.choice(_cfg.SQLI_PAYLOADS)
                resp_time = random.randint(100, 5000) + int(activity * 2000)
                marker = " <== VULNERABLE!" if beat and i == 0 else ""
                line = fit_text(f"  {sqli:50s} [{resp_time:5d}ms]{marker}", width)
            lines.append(line)

    if beat:
        target_table = random.choice(_cfg.DB_TABLES)
        lines.append(fit_text(f"[!] table `{target_table}` dumped -- {random.randint(100, 9999)} rows", width))

    return lines[:height]


# =========================================================================
# 8. VPN TUNNEL
# =========================================================================

def render_vpn_tunnel(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a VPN tunnel visualization with encrypted layers."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    proto = random.choice(_cfg.VPN_PROTOCOLS)
    cipher = random.choice(_cfg.VPN_CIPHERS)

    lines.append(fit_text(f"VPN: {proto}  Cipher: {cipher}", width))
    lines.append(fit_text(f"TUNNEL {meter_bar(activity, bar_w)}", width))

    # Layer diagram (onion-style)
    layers = state.vpn_layers if state and state.vpn_layers else []
    layer_count = min(height - 3, 5)
    for i in range(layer_count):
        if i < len(layers):
            lines.append(fit_text(layers[i], width))
        else:
            indent = " " * (layer_count - i - 1)
            if i == 0:
                # Inner payload
                payload = f"GET /admin HTTP/1.1\\r\\nHost: target.corp"
                line = f"{indent}[ DATA: {payload[:width - len(indent) - 10]} ]"
            elif i == layer_count - 1:
                # Outer encrypted
                enc_val = "".join(random.choice("0123456789ABCDEF") for _ in range(32))
                line = f"{indent}{{{{ ENC: {enc_val} }}}}"
                if beat:
                    line = f"{_cfg.STATUS_CRIT}{line}{_cfg.RESET}"
            else:
                # Mid layers
                hdr = f"TLS {random.choice(['1.2', '1.3', '1.1'])} | Seq: {random.randint(0, 65535)}"
                mid_enc = "".join(random.choice("0123456789ABCDEF") for _ in range(16))
                line = f"{indent}[ {hdr} {mid_enc} ]"
            lines.append(fit_text(line, width))

    latency = int(activity * 200 + random.randint(10, 50))
    lines.append(fit_text(f"Latency: {latency}ms  Jitter: {int(activity * 15)}ms  Loss: {int(activity * 3)}%", width))

    if beat:
        lines.append(fit_text("[!] tunnel renegotiation -- key exchange in progress", width))

    return lines[:height]


# =========================================================================
# 9. DOCKER / K8S
# =========================================================================

def render_docker_k8s(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a container / Kubernetes cluster view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    lines.append(fit_text(f"kubectl get pods -A --context=cluster-{random.choice(['prod', 'staging', 'dev'])}", width))
    lines.append(fit_text(f"CLUSTER {meter_bar(activity, bar_w)}", width))

    pods = state.k8s_pods if state and state.k8s_pods else []
    pod_count = min(height - 3, 6)
    header = f"  {'NAMESPACE':12s} {'NAME':20s} {'IMAGE':24s} {'PHASE':12s} {'IP':16s}"
    lines.append(fit_text(header[:width], width))
    for i in range(pod_count):
        if i < len(pods):
            ns, name, image, phase = pods[i]
        else:
            ns = random.choice(["default", "kube-system", "monitoring", "ingress", "logging"])
            name = f"pod-{random.choice(_cfg.CONTAINER_IMAGES).split(':')[0]}-{random.randint(1, 999)}"
            image = random.choice(_cfg.CONTAINER_IMAGES)
            base_phase = random.choice(_cfg.K8S_POD_PHASES)
            if beat and i == 0:
                phase = "CrashLoopBackOff"
            else:
                phase = base_phase
        ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(2, 254)}"
        line = f"  {ns:12s} {name:20s} {image:24s} {phase:12s} {ip:16s}"
        if "Crash" in phase or "Failed" in phase:
            line = f"{_cfg.STATUS_CRIT}{fit_text(line, width)}{_cfg.RESET}"
        elif phase == "Running":
            line = f"{_cfg.STATUS_OK}{fit_text(line, width)}{_cfg.RESET}"
        else:
            line = fit_text(line, width)
        lines.append(line)

    if beat:
        lines.append(fit_text("[!] container breach -- lateral movement possible", width))

    return lines[:height]


# =========================================================================
# 10. IOT BOTNET
# =========================================================================

def render_iot_botnet(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render an IoT device scan and botnet infection view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    bots = int(activity * 5000)
    lines.append(fit_text(f"zmap -p 23 0.0.0.0/8 --rate=10000", width))
    lines.append(fit_text(f"Devices scanned: {int(activity * 100000):,}  Bots: {bots}", width))
    lines.append(fit_text(f"INFECT {meter_bar(activity, bar_w)}", width))

    devices = state.iot_devices if state and state.iot_devices else []
    dev_count = min(height - 4, 6)
    for i in range(dev_count):
        if i < len(devices):
            dev_type, ip, fw, infected = devices[i]
        else:
            dev_type = random.choice(_cfg.IOT_DEVICE_TYPES)
            ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            fw = random.choice(_cfg.IOT_FIRMWARE)
            infected = random.random() < activity * 0.8
        vuln = random.choice(_cfg.IOT_VULNERABILITIES) if infected else "none"
        marker = f"{_cfg.STATUS_CRIT}[BOT]{_cfg.RESET}" if infected else f"{_cfg.GREEN_DIM}[OK]{_cfg.RESET}"
        line = f"  {marker} {dev_type:14s} {ip:16s} FW:{fw:12s} vuln:{vuln}"
        lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text(f"[!] C2 broadcast -- waking botnet (size: {bots})", width))

    return lines[:height]


# =========================================================================
# 11. PACKET CRAFT
# =========================================================================

def render_packet_craft(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a raw packet crafting view (Scapy-style)."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    proto = random.choice(_cfg.PACKET_PROTOCOLS)
    flags = random.choice(_cfg.TCP_FLAGS) if proto == "TCP" else ""
    src_ip = random_ipv4()
    dst_ip = random_ipv4()
    sport = random.randint(1024, 65535)
    dport = random.choice([22, 80, 443, 8080, 3306, 8443])

    lines.append(fit_text(f"send(IP(src='{src_ip}', dst='{dst_ip}')/{proto}(sport={sport}, dport={dport})", width))
    lines.append(fit_text(f"CRAFT {meter_bar(activity, bar_w)}", width))

    # Hex packet dump
    pkt_lines = state.packet_lines if state and state.packet_lines else []
    pkt_count = min(height - 3, 5)
    for i in range(pkt_count):
        if i < len(pkt_lines):
            lines.append(fit_text(pkt_lines[i], width))
        else:
            if i == 0:
                # Ethernet
                mac = ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))
                line = f"  Eth: {mac:>17s} -> {':'.join(f'{random.randint(0, 255):02x}' for _ in range(6)):17s} 0800"
            elif i == 1:
                # IP
                ver_ihl = "45"
                ttl = random.randint(32, 255)
                ident = f"{random.randint(0, 65535):04x}"
                line = f"  IP:  {ver_ihl}00 {random.randint(20, 100):04x} {ident} {ttl:02x}{random.choice(['06', '11', '01']):2s} {src_ip:>15s} -> {dst_ip:15s}"
            elif i == 2:
                # TCP/UDP
                flags_str = f"[{flags}]" if flags else ""
                seq = random.randint(0, 0xFFFFFFFF)
                ack = random.randint(0, 0xFFFFFFFF)
                line = f"  {proto}: {sport:5d} -> {dport:5d} {flags_str:10s} seq=0x{seq:08x} ack=0x{ack:08x}"
            elif i == 3:
                # Payload hex
                hex_data = " ".join(f"{random.randint(0, 255):02x}" for _ in range(16))
                line = f"  Payload: {hex_data}"
            else:
                ascii_data = "".join(chr(random.randint(32, 126)) if random.random() < 0.7 else "." for _ in range(16))
                line = f"  ASCII:   |{ascii_data}|"

            if beat and i == 2:
                line = f"{_cfg.STATUS_CRIT}{fit_text(line, width)}{_cfg.RESET}"
            else:
                line = fit_text(line, width)
            lines.append(line)

    if beat:
        lines.append(fit_text("[!] crafted packet sent -- awaiting response", width))

    return lines[:height]


# =========================================================================
# 12. STEGO DETECT
# =========================================================================

def render_stego_detect(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a steganography detection / analysis view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    fmt = random.choice(_cfg.STEGO_FORMATS)
    algo = random.choice(_cfg.STEGO_ALGORITHMS)

    lines.append(fit_text(f"stegdetect --format={fmt} --algo={algo} suspicious.{fmt.lower()}", width))
    lines.append(fit_text(f"ANALYZE {meter_bar(activity, bar_w)}", width))

    lines.append(fit_text(f"File: {random.choice(['img_', 'photo_', 'secret_', 'payload_'])}{random.randint(1000, 9999)}.{fmt.lower()}", width))

    # LSB analysis histogram
    samples = state.stego_lines if state and state.stego_lines else []
    sample_count = min(height - 4, 5)
    for i in range(sample_count):
        if i < len(samples):
            lines.append(fit_text(samples[i], width))
        else:
            # LSB value distribution
            lsb_vals = [random.randint(0, 1) for _ in range(max(10, width - 20))]
            lsb_str = "".join(str(v) for v in lsb_vals)
            analysis = ""
            if i == 0:
                analysis = f"LSB Analysis: {lsb_str[:width - 20]}"
            elif i == 1:
                # Chi-square
                chi = random.random() * activity * 100
                analysis = f"Chi-square: {chi:.2f}  p-value: {random.random() * (1 - activity):.4f}"
                if chi > 50:
                    analysis = f"{_cfg.STATUS_CRIT}{analysis}{_cfg.RESET}"
            elif i == 2:
                # Entropy
                entropy = 4.0 + activity * 4.0
                analysis = f"Entropy: {entropy:.2f} bits/byte  (threshold: 7.5)"
            elif i == 3:
                analysis = f"Color histogram deviation: {int(activity * 100)}%"
            else:
                analysis = f"Embedded payload size: {int(activity * 1024)} bytes estimated"
            lines.append(fit_text(analysis, width))

    if beat:
        lines.append(fit_text(f"[+] hidden payload detected via {algo}", width))

    return lines[:height]


# =========================================================================
# 13. CRACK MAP
# =========================================================================

def render_crack_map(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a password cracking heatmap / status view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    total_hashes = random.randint(1000, 50000)
    cracked = int(total_hashes * activity * random.uniform(0.5, 0.9))
    rate = (activity * 5000 + random.randint(100, 1000)) / 1000.0

    lines.append(fit_text(f"hashcat -m 0 -a 3 hashes.txt ?a?a?a?a --speed-only", width))
    lines.append(fit_text(f"Hashes: {total_hashes:,}  Cracked: {cracked:,}  Rate: {rate:.1f}M/s", width))
    lines.append(fit_text(f"CRACK {meter_bar(activity, bar_w)}", width))

    rows = state.crack_rows if state and state.crack_rows else []
    row_count = min(height - 4, 6)
    last_algo = random.choice(_cfg.HASH_TYPES)
    header = f"  {'ALGO':12s} {'HASH':36s} {'CRACKED':8s} {'TOTAL':8s} {'RATE':6s}"
    lines.append(fit_text(header[:width], width))
    for i in range(row_count):
        if i < len(rows):
            algo, hsh, cr, tot, rt = rows[i]
        else:
            algo = random.choice(_cfg.HASH_TYPES)
            last_algo = algo
            hsh = "".join(random.choice("0123456789abcdef") for _ in range(32))
            cr = int(activity * random.randint(100, 9000))
            tot = cr + random.randint(100, 5000)
            rt = (activity * random.uniform(1, 10)) / 1000.0
        pct = (cr / max(1, tot)) * 100
        line = f"  {algo:12s} {hsh:36s} {cr:8d} {tot:8d} {rt:.2f}M/s"
        if pct > 90:
            line = f"{_cfg.STATUS_OK}{fit_text(line, width)}{_cfg.RESET}"
        elif pct > 50:
            line = f"{_cfg.STATUS_WARN}{fit_text(line, width)}{_cfg.RESET}"
        else:
            line = fit_text(line, width)
        lines.append(line)

    if beat:
        lines.append(fit_text(f"[+] {last_algo} master key recovered ({cracked}/{total_hashes})", width))

    return lines[:height]


# =========================================================================
# 14. AURORA
# =========================================================================

def render_aurora(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render an animated aurora borealis effect using ANSI colors."""
    from cmd_audio.utils import clamp as _clamp

    lines: List[str] = []
    activity = _clamp(module_level if module_level is not None else level, 0.0, 1.0)

    grid: List[List[str]] = [[" "] * width for _ in range(height)]

    # Aurora bands
    bands_count = 3 + int(activity * 4)
    for b in range(bands_count):
        color = random.choice(_cfg.AURORA_COLORS)
        y_base = int((b / max(1, bands_count)) * height * 0.6)
        wave_amp = 2 + int(activity * 4)
        wave_freq = 0.2 + random.random() * 0.3
        wave_offset = random.random() * 100
        for x in range(width):
            y_offset = int(math.sin(x * wave_freq + wave_offset) * wave_amp)
            y = y_base + y_offset
            if 0 <= y < height:
                intensity = random.random() < (activity * 0.5)
                if intensity:
                    ch = random.choice([".", ":", "~", "-", "+", "*"])
                    grid[y][x] = f"{color}{ch}{_cfg.RESET}"

    # Bright streaks on beat
    if beat:
        for _ in range(3):
            streak_y = random.randint(0, height // 2)
            streak_x = random.randint(0, width - 20)
            streak_len = random.randint(10, 30)
            for dx in range(streak_len):
                if streak_x + dx < width:
                    grid[streak_y][streak_x + dx] = f"{_cfg.GREEN_BRIGHT}*{_cfg.RESET}"

    for row in grid:
        lines.append("".join(row))

    return lines[:height]


# =========================================================================
# 15. BIOS / POST
# =========================================================================

def render_bios_poste(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a system boot / POST sequence."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)

    vendor = random.choice(_cfg.BIOS_VENDORS)
    cpu = random.choice(_cfg.BIOS_CPUS)
    ram_total = random.choice([4096, 8192, 16384, 32768, 65536])
    ram_detected = int(ram_total * min(1.0, activity * 1.2))

    lines.append(fit_text(f" {vendor} BIOS PnP {random.choice(['1.0A', '2.1', '3.0', '4.0'])}", width))
    lines.append(fit_text(f" CPU: {cpu:40s}  Cache: {random.randint(8, 64)}MB", width))

    # POST component check
    comps = state.bios_lines if state and state.bios_lines else []
    comp_count = min(height - 4, 8)
    for i in range(comp_count):
        if i < len(comps):
            lines.append(fit_text(comps[i], width))
        else:
            comp = random.choice(_cfg.BIOS_COMPONENTS)
            if random.random() < activity * 0.9 or (beat and i == comp_count - 1):
                if beat and i == comp_count - 1:
                    status = f"{_cfg.STATUS_CRIT}[FAIL]{_cfg.RESET}"
                    msg = f" {comp:12s} {status} -- CHECKSUM ERROR"
                else:
                    status = f"{_cfg.STATUS_OK}[PASS]{_cfg.RESET}"
                    msg = f" {comp:12s} {status}"
            else:
                status = f"{_cfg.GREEN_DIM}[SKIP]{_cfg.RESET}"
                msg = f" {comp:12s} {status}"
            lines.append(fit_text(msg, width))

    # RAM test
    ram_bar_w = max(6, width - 24)
    lines.append(fit_text(f" RAM Testing: {ram_detected:6d}MB / {ram_total:6d}MB {meter_bar(ram_detected / max(1, ram_total), ram_bar_w)}", width))

    if beat:
        lines.append(fit_text(f" {_cfg.STATUS_CRIT}[!] CMOS CHECKSUM INVALID -- SYSTEM HALTED{_cfg.RESET}", width))

    return lines[:height]


# =========================================================================
# 16. MORSE CODE
# =========================================================================

def render_morse_code(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a Morse code decoder with waveform and decoded text."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    # Generate a random message and encode to morse
    words = ["SOS", "ADMIN", "ROOT", "SHELL", "ALERT", "ACCESS", "HACK", "DATA", "EXFIL", "PWN"]
    msg_words = [random.choice(words) for _ in range(max(1, height // 3))]
    message = " ".join(msg_words)

    morse_parts = []
    for ch in message.upper():
        code = _cfg.MORSE_ALPHABET.get(ch, " ")
        morse_parts.append(code)
    morse_str = " ".join(morse_parts)

    lines.append(fit_text(f"Morse decoder -- freq: {random.choice(['800Hz', '1200Hz', '600Hz'])}", width))
    lines.append(fit_text(f"Signal SNR: {int(activity * 30 + 10):2d}dB  Rate: {random.choice(['5', '12', '20', '30'])}wpm", width))
    lines.append(fit_text(f"DECODE {meter_bar(activity, bar_w)}", width))

    # Waveform
    rows_remaining = height - len(lines)
    for i in range(rows_remaining):
        if i == 0:
            # Signal waveform
            wave = ""
            for x in range(width):
                val = math.sin(x * 0.3 + activity * 10) * activity
                if abs(val) > 0.3:
                    wave += _cfg.GREEN_BRIGHT + "#" + _cfg.RESET if val > 0 else _cfg.GREEN_DIM + "." + _cfg.RESET
                else:
                    wave += " "
            lines.append(wave)
        elif i <= len(morse_str) // width + 1:
            idx = (i - 1) * width
            segment = morse_str[idx:idx + width]
            if beat and i == 1:
                segment = f"{_cfg.STATUS_CRIT}{segment}{_cfg.RESET}"
            lines.append(fit_text(segment, width))
        else:
            lines.append(fit_text(f"Decoded: {message[:width - 12]}", width))
            break
        if len(lines) >= height:
            break

    return lines[:height]


# =========================================================================
# 17. WHOIS SCAN
# =========================================================================

def render_whois_scan(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render a Whois / domain lookup view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    domain = f"{random.choice(['target', 'corp', 'megacorp', 'darknet', 'shadow', 'cyberdyne'])}{random.choice(_cfg.TLD_LIST)}"
    registrar = random.choice(_cfg.REGISTRARS)
    creation = f"20{random.randint(10, 25)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    expiry = f"20{random.randint(26, 30)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

    lines.append(fit_text(f"whois {domain}", width))
    lines.append(fit_text(f"LOOKUP {meter_bar(activity, bar_w)}", width))

    rows = state.whois_data if state and state.whois_data else []
    row_count = min(height - 3, 8)
    for i in range(row_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            if i == 0:
                line = f"  Domain: {domain}"
            elif i == 1:
                line = f"  Registrar: {registrar}"
            elif i == 2:
                line = f"  Creation: {creation}  Expiry: {expiry}"
            elif i == 3:
                nameservers = f"ns1.{domain.replace('.', '.')}  ns2.{domain.replace('.', '.')}"
                line = f"  Name Servers: {nameservers}"
            elif i == 4:
                statuses = random.choice(["clientTransferProhibited", "clientDeleteProhibited", "addPeriod", "ok", "inactive"])
                line = f"  Status: {statuses}"
            elif i == 5:
                org = f"{random.choice(['Acme', 'Global', 'Shadow', 'Cyber', 'Dark']) } {random.choice(['Corp', 'Inc', 'LLC', 'Ltd', 'Enterprises'])}"
                line = f"  Organization: {org}"
            elif i == 6:
                line = f"  Abuse Contact: abuse@{domain.split('.')[0]}.{domain.split('.')[1]}"
            else:
                names = ", ".join(random.choice([f"admin@email.com", f"hostmaster@{domain}", f"noc@{domain}"]) for _ in range(2))
                line = f"  Contacts: {names}"
            lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text("[!] WHOIS privacy shield detected -- proxying request", width))

    return lines[:height]


# =========================================================================
# 18. CERT SCRAPE
# =========================================================================

def render_cert_scrape(
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState] = None,
    module_level: Optional[float] = None,
) -> List[str]:
    """Render an SSL/TLS certificate inspection view."""
    lines: List[str] = []
    activity = clamp(module_level if module_level is not None else level, 0.0, 1.0)
    bar_w = max(8, width - 18)

    domain = f"{random.choice(['www', 'api', 'mail', 'admin', 'vpn'])}.{random.choice(['target', 'corp', 'megacorp', 'darknet', 'shadow'])}{random.choice(_cfg.TLD_LIST)}"
    issuer = random.choice(_cfg.CERT_ISSUERS)
    cipher = random.choice(_cfg.SSL_CIPHERS)
    proto = random.choice(_cfg.SSL_PROTOCOLS)
    key_algo = random.choice(_cfg.SSL_KEY_ALGOS)

    lines.append(fit_text(f"openssl s_client -connect {domain}:443 -showcerts", width))
    lines.append(fit_text(f"CERT SCAN {meter_bar(activity, bar_w)}", width))

    rows = state.cert_data if state and state.cert_data else []
    row_count = min(height - 3, 8)
    for i in range(row_count):
        if i < len(rows):
            lines.append(fit_text(rows[i], width))
        else:
            if i == 0:
                serial = "".join(random.choice("0123456789ABCDEF") for _ in range(32))
                line = f"  Serial: {serial}"
            elif i == 1:
                line = f"  Issuer: {issuer}"
            elif i == 2:
                cn = domain
                org = f"{random.choice(['Acme', 'Global', 'Shadow']) } {random.choice(['Corp', 'Inc'])}"
                line = f"  Subject: CN={cn}, O={org}"
            elif i == 3:
                valid_from = f"Jan  1 00:00:00 20{random.randint(22, 25)} GMT"
                valid_to = f"Dec 31 23:59:59 20{random.randint(26, 28)} GMT"
                remaining = random.randint(30, 365)
                marker = f" {_cfg.STATUS_CRIT}[EXPIRING]{_cfg.RESET}" if remaining < 60 else ""
                line = f"  Validity: {valid_from} -> {valid_to} ({remaining}d remaining){marker}"
            elif i == 4:
                line = f"  Public Key: {key_algo}"
            elif i == 5:
                fingerprints = [f"SHA256: {''.join(random.choice('0123456789ABCDEF') for _ in range(64))}",
                               f"SHA1:   {''.join(random.choice('0123456789ABCDEF') for _ in range(40))}"]
                line = f"  Fingerprints: {fingerprints[0]}"
            elif i == 6:
                line = f"  Cipher: {cipher}  Protocol: {proto}"
            else:
                sans = ", ".join(f"DNS:{sub}.{domain.split('.')[-2]}.{domain.split('.')[-1]}" for sub in random.sample(['www', 'api', 'mail', 'admin', 'vpn', 'dev', 'staging', 'cdn'], 3))
                line = f"  Subject Alt Names: {sans}"
            lines.append(fit_text(line, width))

    if beat:
        lines.append(fit_text(f"[!] certificate pinning bypassed -- MITM position gained", width))

    return lines[:height]


# ---------------------------------------------------------------------------
# Existing render functions (unchanged)
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
    elif mode == "buffer-overflow":
        return render_buffer_overflow(level, beat, width, height)
    elif mode == "geo-trace":
        return render_geo_trace(level, beat, width, height)
    elif mode == "vhs-glitch":
        return render_vhs_glitch(level, beat, width, height)
    elif mode == "radar-sweep":
        return render_radar_sweep(level, beat, width, height)
    elif mode == "particle-storm":
        return render_particle_storm(level, beat, width, height)
    elif mode == "payload":
        return render_payload_builder(level, beat, width, height)
    elif mode == "sql-injection":
        return render_sql_injection(level, beat, width, height)
    elif mode == "vpn-tunnel":
        return render_vpn_tunnel(level, beat, width, height)
    elif mode == "docker-k8s":
        return render_docker_k8s(level, beat, width, height)
    elif mode == "iot-botnet":
        return render_iot_botnet(level, beat, width, height)
    elif mode == "packet-craft":
        return render_packet_craft(level, beat, width, height)
    elif mode == "stego-detect":
        return render_stego_detect(level, beat, width, height)
    elif mode == "crack-map":
        return render_crack_map(level, beat, width, height)
    elif mode == "aurora":
        return render_aurora(level, beat, width, height)
    elif mode == "bios-poste":
        return render_bios_poste(level, beat, width, height)
    elif mode == "morse-code":
        return render_morse_code(level, beat, width, height)
    elif mode == "whois-scan":
        return render_whois_scan(level, beat, width, height)
    elif mode == "cert-scrape":
        return render_cert_scrape(level, beat, width, height)
    else:
        return build_spectrum_lines(bands, width, height, history, shell_lines, quality_scale)


# All available visual module names for cycling
ALL_VISUAL_MODULES = [
    "nodes", "files", "firewall", "ports", "crypto", "admin",
    "processes", "traffic", "syslog", "filesystem", "ssh-brute",
    "dns", "db-dump", "memory",
    "buffer-overflow", "geo-trace", "vhs-glitch", "radar-sweep",
    "particle-storm", "payload", "sql-injection", "vpn-tunnel",
    "docker-k8s", "iot-botnet", "packet-craft", "stego-detect",
    "crack-map", "aurora", "bios-poste", "morse-code",
    "whois-scan", "cert-scrape",
]

# Default set of 4 modules to show at any time
DEFAULT_VISUAL_MODULES = ["nodes", "firewall", "ports", "crypto"]


def get_visual_modules_for_cycle(cycle_idx: int, count: int = 4) -> List[str]:
    """Return a list of module names for the given cycle index."""
    n = len(ALL_VISUAL_MODULES)
    start = (cycle_idx * count) % n
    result = []
    for i in range(count):
        result.append(ALL_VISUAL_MODULES[(start + i) % n])
    return result


def render_visual_module(
    module_name: str,
    level: float,
    beat: bool,
    width: int,
    height: int,
    state: Optional[VisualState],
    module_levels: Dict[str, float],
) -> List[str]:
    """Render a single visual module by name."""
    ml = module_levels.get(module_name, level)
    if module_name == "nodes":
        return render_network_nodes(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "files":
        return render_file_transfer(level, width, height, state=state, module_level=ml)
    elif module_name == "firewall":
        return render_firewall_status(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "crypto":
        return render_encryption_crack(level, width, height, state=state, module_level=ml)
    elif module_name == "ports":
        return render_port_scan(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "admin":
        return render_admin_alerts(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "processes":
        return render_process_monitor(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "traffic":
        return render_network_traffic(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "syslog":
        return render_system_log(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "filesystem":
        return render_filesystem(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "ssh-brute":
        return render_ssh_bruteforce(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "dns":
        return render_dns_enum(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "db-dump":
        return render_db_dump(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "memory":
        return render_memory_analysis(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "buffer-overflow":
        return render_buffer_overflow(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "geo-trace":
        return render_geo_trace(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "vhs-glitch":
        return render_vhs_glitch(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "radar-sweep":
        return render_radar_sweep(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "particle-storm":
        return render_particle_storm(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "payload":
        return render_payload_builder(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "sql-injection":
        return render_sql_injection(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "vpn-tunnel":
        return render_vpn_tunnel(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "docker-k8s":
        return render_docker_k8s(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "iot-botnet":
        return render_iot_botnet(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "packet-craft":
        return render_packet_craft(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "stego-detect":
        return render_stego_detect(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "crack-map":
        return render_crack_map(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "aurora":
        return render_aurora(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "bios-poste":
        return render_bios_poste(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "morse-code":
        return render_morse_code(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "whois-scan":
        return render_whois_scan(level, beat, width, height, state=state, module_level=ml)
    elif module_name == "cert-scrape":
        return render_cert_scrape(level, beat, width, height, state=state, module_level=ml)
    else:
        return render_network_nodes(level, beat, width, height, state=state, module_level=ml)


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
    active_modules: Optional[List[str]] = None,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Render separate Hacknet feeds sized for embedding in a composed center panel."""
    del bands, history, shell_lines, quality_scale
    panel_w = max(10, width)
    panel_h = max(2, height)

    if active_modules is None:
        active_modules = DEFAULT_VISUAL_MODULES

    # Ensure we always return exactly 4 panels
    while len(active_modules) < 4:
        active_modules.append(active_modules[-1] if active_modules else "nodes")

    results = []
    for mod in active_modules[:4]:
        results.append(render_visual_module(mod, level, beat, panel_w, panel_h, state, module_levels))

    return tuple(results)  # type: ignore[return-value]


def compose_center_panel(
    center_w: int,
    center_h: int,
    nodes: List[str],
    firewall: List[str],
    ports: List[str],
    crypto: List[str],
    module_names: Optional[List[str]] = None,
) -> List[str]:
    """Compose four separated hacking modules into a single center panel body."""
    if center_h <= 0:
        return []

    out: List[str] = []
    if module_names is None:
        module_names = ["nodes", "firewall", "ports", "crypto"]
    all_lines = [nodes, firewall, ports, crypto]
    sections = list(zip(module_names, all_lines))
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

    # --- 18 new modules state refresh ---

    if random.random() < (0.12 + (0.40 * module_levels.get("buffer-overflow", 0.0))):
        state.buffer_overflow_stack = [
            f"    [buffer overflow exploit ready]",
            f"    shellcode size: {random.randint(128, 1024)} bytes",
            f"    NOP sled length: {int(module_levels.get('buffer-overflow', 0.0) * 128 + 16)}",
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("geo-trace", 0.0))):
        state.geo_trace_hops = []

    if random.random() < (0.12 + (0.40 * module_levels.get("vhs-glitch", 0.0))):
        state.vhs_lines = []

    if random.random() < (0.12 + (0.40 * module_levels.get("radar-sweep", 0.0))):
        activity = module_levels.get("radar-sweep", 0.0)
        state.radar_blips = [
            (random.random() * 360, random.random() * 0.9,
             random.choice(_cfg.RADAR_BLIP_TYPES), random.random())
            for _ in range(int(activity * 5 + 2))
        ]

    if random.random() < (0.15 + (0.45 * module_levels.get("particle-storm", 0.0))):
        state.particle_stars = []

    if random.random() < (0.12 + (0.40 * module_levels.get("payload", 0.0))):
        state.payload_lines = [
            f"  0x{0x08040000 + i * 16:08x}: {' '.join(f'{random.randint(0, 255):02x}' for _ in range(16))}  |{''.join(chr(random.randint(32, 126)) if random.random() < 0.7 else '.' for _ in range(16))}|"
            for i in range(5)
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("sql-injection", 0.0))):
        state.sqli_lines = [
            f"  {random.choice(_cfg.SQLI_PAYLOADS):50s} [{random.randint(100, 5000):5d}ms]"
            for _ in range(4)
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("vpn-tunnel", 0.0))):
        state.vpn_layers = []

    if random.random() < (0.14 + (0.40 * module_levels.get("docker-k8s", 0.0))):
        state.k8s_pods = [
            (random.choice(["default", "kube-system", "monitoring", "ingress"]),
             f"pod-{random.choice(_cfg.CONTAINER_IMAGES).split(':')[0]}-{random.randint(1, 999)}",
             random.choice(_cfg.CONTAINER_IMAGES),
             random.choice(_cfg.K8S_POD_PHASES))
            for _ in range(6)
        ]

    if random.random() < (0.13 + (0.40 * module_levels.get("iot-botnet", 0.0))):
        state.iot_devices = [
            (random.choice(_cfg.IOT_DEVICE_TYPES),
             f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
             random.choice(_cfg.IOT_FIRMWARE),
             random.random() < module_levels.get("iot-botnet", 0.0) * 0.8)
            for _ in range(6)
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("packet-craft", 0.0))):
        state.packet_lines = []

    if random.random() < (0.12 + (0.40 * module_levels.get("stego-detect", 0.0))):
        state.stego_lines = []

    if random.random() < (0.13 + (0.40 * module_levels.get("crack-map", 0.0))):
        state.crack_rows = [
            (random.choice(_cfg.HASH_TYPES),
             "".join(random.choice("0123456789abcdef") for _ in range(32)),
             int(module_levels.get("crack-map", 0.0) * random.randint(100, 9000)),
             random.randint(1000, 50000),
             module_levels.get("crack-map", 0.0) * random.uniform(1, 10) / 1000.0)
            for _ in range(6)
        ]

    if random.random() < (0.12 + (0.40 * module_levels.get("aurora", 0.0))):
        state.aurora_buf = []

    if random.random() < (0.12 + (0.40 * module_levels.get("bios-poste", 0.0))):
        state.bios_lines = []

    if random.random() < (0.12 + (0.40 * module_levels.get("morse-code", 0.0))):
        state.morse_lines = []

    if random.random() < (0.12 + (0.40 * module_levels.get("whois-scan", 0.0))):
        state.whois_data = []

    if random.random() < (0.12 + (0.40 * module_levels.get("cert-scrape", 0.0))):
        state.cert_data = []

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
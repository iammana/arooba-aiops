"""
Visual RF & Campus Floorplan Heatmap Generator for Arooba-AIOps.
Renders an architectural floorplan with AP RF propagation cells,
live station associations, sticky client roaming vectors,
UXI synthetic probes, and WIDS rogue AP detection.
"""

from typing import List, Dict, Any, Optional
from simulator.models import AccessPoint, ClientStation, SecurityThreat, UxiSensorReport


def generate_floorplan_svg(
    aps: List[AccessPoint],
    clients: List[ClientStation],
    threats: List[SecurityThreat],
    uxi_report: Optional[UxiSensorReport] = None,
) -> str:
    """
    Generates a dark-themed SVG floorplan of Montreal HQ campus.
    Coordinates: viewBox 0 0 900 520
    """
    svg_parts = []

    # SVG Header and Definitions
    svg_parts.append(
        """<svg viewBox="0 0 900 520" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="background-color: #0e1117; border-radius: 10px; border: 1px solid #30363d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <!-- RF Signal Gradient (Healthy) -->
    <radialGradient id="rf-healthy" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00e676" stop-opacity="0.35"/>
      <stop offset="60%" stop-color="#00e676" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#00e676" stop-opacity="0.0"/>
    </radialGradient>

    <!-- RF Signal Gradient (Congested / High Power) -->
    <radialGradient id="rf-congested" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff9100" stop-opacity="0.45"/>
      <stop offset="65%" stop-color="#ff9100" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#ff9100" stop-opacity="0.0"/>
    </radialGradient>

    <!-- Rogue AP Threat Gradient -->
    <radialGradient id="rf-threat" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff1744" stop-opacity="0.5"/>
      <stop offset="60%" stop-color="#ff1744" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#ff1744" stop-opacity="0.0"/>
    </radialGradient>

    <!-- Drop Shadows -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <style>
      @keyframes pulse-threat {
        0% { r: 50px; opacity: 0.6; }
        50% { r: 85px; opacity: 0.2; }
        100% { r: 50px; opacity: 0.6; }
      }
      @keyframes dash-sticky {
        to { stroke-dashoffset: -20; }
      }
      .threat-pulse { animation: pulse-threat 2s infinite ease-in-out; }
      .sticky-link { animation: dash-sticky 1s linear infinite; }
    </style>
  </defs>
"""
    )

    # 1. Architectural Floorplan Blueprint (Rooms & Walls)
    svg_parts.append(
        """
  <!-- Blueprint Grid -->
  <g stroke="#1c2128" stroke-width="0.5">
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#161b22" stroke-width="0.8"/>
    </pattern>
    <rect width="900" height="520" fill="url(#grid)"/>
  </g>

  <!-- Campus Building Layout -->
  <!-- Outer Boundary Wall -->
  <rect x="30" y="30" width="840" height="460" rx="8" fill="#13171f" stroke="#38444d" stroke-width="2.5"/>

  <!-- Zone 1: Breakout Lounge & Cafeteria (Top Left) -->
  <rect x="30" y="30" width="280" height="210" fill="#171c26" stroke="#2d333b" stroke-width="1.5"/>
  <text x="45" y="55" fill="#8b949e" font-size="12" font-weight="600">ZONE 1: LOUNGE &amp; CAFETERIA</text>
  <text x="45" y="72" fill="#58a6ff" font-size="10">802.11ax Public / Guest</text>

  <!-- Zone 2: Ground Floor Lobby (Bottom Left) -->
  <rect x="30" y="240" width="280" height="250" fill="#151a24" stroke="#2d333b" stroke-width="1.5"/>
  <text x="45" y="265" fill="#8b949e" font-size="12" font-weight="600">ZONE 2: MAIN LOBBY &amp; RECEPTION</text>
  <text x="45" y="282" fill="#58a6ff" font-size="10">Ground Floor Entrance • High Foot-Traffic</text>

  <!-- Zone 3: Executive Conference Room B (Top Center) -->
  <rect x="310" y="30" width="280" height="210" fill="#181e2b" stroke="#388bfd" stroke-width="1.8" stroke-dasharray="4,2"/>
  <text x="325" y="55" fill="#58a6ff" font-size="12" font-weight="600">ZONE 3: EXECUTIVE CONF ROOM B</text>
  <text x="325" y="72" fill="#8b949e" font-size="10">Ultra HD Video Conferencing &amp; Zoom</text>

  <!-- Zone 4: Central Collaboration Atrium (Bottom Center) -->
  <rect x="310" y="240" width="280" height="250" fill="#161b24" stroke="#2d333b" stroke-width="1.5"/>
  <text x="325" y="265" fill="#8b949e" font-size="12" font-weight="600">ZONE 4: COLLABORATION ATRIUM</text>
  <text x="325" y="282" fill="#8b949e" font-size="10">Open Seating &amp; Hot Desks</text>

  <!-- Zone 5: Engineering & QA Lab (Right Wing) -->
  <rect x="590" y="30" width="280" height="460" fill="#171c26" stroke="#2d333b" stroke-width="1.5"/>
  <text x="605" y="55" fill="#8b949e" font-size="12" font-weight="600">ZONE 5: ENGINEERING &amp; QA LAB</text>
  <text x="605" y="72" fill="#58a6ff" font-size="10">High-Density Wi-Fi 6E (6GHz / 160MHz)</text>
"""
    )

    # Lookup mapping for AP positions
    ap_map: Dict[str, Dict[str, Any]] = {}

    # 2. Render RF Propagation Heatmap for Access Points
    for ap in aps:
        # Scale pos_x and pos_y (0-100) to floorplan (30-870, 30-490)
        cx = 30 + (ap.pos_x / 100.0) * 840
        cy = 30 + (ap.pos_y / 100.0) * 460

        ap_map[ap.name] = {"x": cx, "y": cy, "ap": ap}
        ap_map[ap.ap_id] = {"x": cx, "y": cy, "ap": ap}

        # Calculate RF radius based on Tx power (Log-distance path loss approximation)
        tx_pwr = max(ap.tx_power_2g_dbm, ap.tx_power_5g_dbm)
        r_coverage = 90 + (tx_pwr - 14) * 8
        is_congested = ap.channel_utilization_pct > 70.0
        grad_id = "rf-congested" if is_congested else "rf-healthy"

        # RF Propagation circles (Gradient cells)
        svg_parts.append(
            f"""
  <!-- RF Coverage: {ap.name} -->
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_coverage:.1f}" fill="url(#{grad_id})" />
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_coverage*0.5:.1f}" fill="none" stroke="{'#ff9100' if is_congested else '#00e676'}" stroke-width="1" stroke-dasharray="3,3" opacity="0.4"/>
"""
        )

    # 3. Render Rogue AP / Threats if present
    for threat in threats:
        tx = 450.0  # Default near Conf Room B
        ty = 160.0
        if "conf" in threat.detecting_ap.lower() or "b" in threat.detecting_ap.lower():
            tx = 440.0
            ty = 150.0

        svg_parts.append(
            f"""
  <!-- Rogue AP Threat: {threat.bssid} -->
  <circle cx="{tx}" cy="{ty}" r="65" class="threat-pulse" fill="url(#rf-threat)" />
  <circle cx="{tx}" cy="{ty}" r="16" fill="#b71c1c" stroke="#ff1744" stroke-width="2" filter="url(#glow)"/>
  <text x="{tx}" y="{ty+5}" fill="#ffffff" font-size="12" font-weight="900" text-anchor="middle">☠</text>
  <rect x="{tx-90}" y="{ty+22}" width="180" height="34" rx="4" fill="#210508" stroke="#ff1744" stroke-width="1"/>
  <text x="{tx}" y="{ty+36}" fill="#ff5252" font-size="10" font-weight="700" text-anchor="middle">ROGUE AP: {threat.ssid}</text>
  <text x="{tx}" y="{ty+49}" fill="#ff8a80" font-size="9" text-anchor="middle">BSSID: {threat.bssid} ({'CONTAINED' if threat.is_contained else 'ACTIVE'})</text>
"""
        )

    # 4. Render Client Association Links (Lines from station to AP)
    for c in clients:
        cx = 30 + (c.pos_x / 100.0) * 840
        cy = 30 + (c.pos_y / 100.0) * 460

        target_ap = ap_map.get(c.ap_name)
        if target_ap:
            ap_x, ap_y = target_ap["x"], target_ap["y"]

            if c.sticky_client_detected or c.rssi_dbm < -75:
                # Sticky client: Long dashed red/orange line spanning across rooms!
                svg_parts.append(
                    f"""
  <!-- Sticky Roaming Failure Link -->
  <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ap_x:.1f}" y2="{ap_y:.1f}" stroke="#ff3d00" stroke-width="2.5" stroke-dasharray="6,4" class="sticky-link" opacity="0.85"/>
  <!-- Roam Target Vector Indicator (Near Conf Room B AP) -->
  <line x1="{cx:.1f}" y1="{cy:.1f}" x2="450" y2="170" stroke="#00e676" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.5"/>
  <text x="{(cx+ap_x)/2:.1f}" y="{(cy+ap_y)/2 - 8:.1f}" fill="#ff5722" font-size="10" font-weight="700" text-anchor="middle">⚠️ STICKY CLIENT ({c.rssi_dbm} dBm)</text>
"""
                )
            else:
                # Normal healthy link
                svg_parts.append(
                    f"""
  <!-- Station Link: {c.hostname} -->
  <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ap_x:.1f}" y2="{ap_y:.1f}" stroke="#00e676" stroke-width="1.2" stroke-dasharray="2,2" opacity="0.35"/>
"""
                )

    # 5. Render Access Point Radios Icons & Details
    for ap in aps:
        info = ap_map[ap.name]
        cx, cy = info["x"], info["y"]
        is_congested = ap.channel_utilization_pct > 70.0
        ap_color = "#ff9100" if is_congested else "#00e676"
        badge_bg = "#2e1a00" if is_congested else "#0a2618"

        svg_parts.append(
            f"""
  <!-- AP Hardware Node: {ap.name} -->
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="18" fill="#1f242e" stroke="{ap_color}" stroke-width="2.5" filter="url(#glow)"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{ap_color}"/>
  <text x="{cx:.1f}" y="{cy-26:.1f}" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">{ap.name}</text>
  <!-- Telemetry Badge -->
  <rect x="{cx-75:.1f}" y="{cy+24:.1f}" width="150" height="34" rx="4" fill="{badge_bg}" stroke="{ap_color}" stroke-width="1"/>
  <text x="{cx:.1f}" y="{cy+38:.1f}" fill="{ap_color}" font-size="10" font-weight="700" text-anchor="middle">Ch {ap.channel_2g} (2.4G) | Ch {ap.channel_5g} (5G)</text>
  <text x="{cx:.1f}" y="{cy+51:.1f}" fill="#8b949e" font-size="9" text-anchor="middle">Airtime: {ap.channel_utilization_pct}% • {len(ap.connected_clients)} Clients</text>
"""
        )

    # 6. Render Client Station Icons & Tags
    for c in clients:
        cx = 30 + (c.pos_x / 100.0) * 840
        cy = 30 + (c.pos_y / 100.0) * 460

        is_sticky = c.sticky_client_detected or c.rssi_dbm < -75
        is_dhcp_fail = c.connection_state.value == "DHCP_FAILED"

        sta_color = "#ff3d00" if (is_sticky or is_dhcp_fail) else "#00e5ff"
        icon_symbol = "!" if is_dhcp_fail else ("⚡" if is_sticky else "💻")

        svg_parts.append(
            f"""
  <!-- Client Station: {c.hostname} -->
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#1b2028" stroke="{sta_color}" stroke-width="2"/>
  <text x="{cx:.1f}" y="{cy+3.5:.1f}" fill="{sta_color}" font-size="9" text-anchor="middle">{icon_symbol}</text>
  <text x="{cx:.1f}" y="{cy-12:.1f}" fill="#e6edf3" font-size="10" font-weight="600" text-anchor="middle">{c.hostname}</text>
  <text x="{cx:.1f}" y="{cy+21:.1f}" fill="{sta_color}" font-size="9" text-anchor="middle">{c.rssi_dbm} dBm ({c.band})</text>
"""
        )

    # 7. Render UXI Sensor Probe
    uxi_sla = uxi_report.overall_sla if uxi_report else "PASSED"
    uxi_color = "#ff1744" if uxi_sla == "FAILED" else ("#ff9100" if uxi_sla == "DEGRADED" else "#d500f9")
    svg_parts.append(
        f"""
  <!-- Synthetic UXI Sensor Probe -->
  <g transform="translate(330, 160)">
    <rect x="0" y="0" width="130" height="42" rx="6" fill="#1b122c" stroke="{uxi_color}" stroke-width="1.5"/>
    <circle cx="15" cy="21" r="7" fill="{uxi_color}" filter="url(#glow)"/>
    <text x="28" y="18" fill="#e1bee7" font-size="10" font-weight="700">UXI Probe Sensor</text>
    <text x="28" y="32" fill="{uxi_color}" font-size="9" font-weight="600">SLA: {uxi_sla}</text>
  </g>
"""
    )

    # Floorplan Legend Bar at Bottom
    svg_parts.append(
        """
  <!-- Legend Bar -->
  <rect x="30" y="480" width="840" height="25" rx="4" fill="#0d1117" stroke="#21262d" stroke-width="1"/>
  <circle cx="50" cy="492" r="5" fill="#00e676"/>
  <text x="62" y="496" fill="#8b949e" font-size="10">Clean 802.11 RF Cell</text>

  <circle cx="190" cy="492" r="5" fill="#ff9100"/>
  <text x="202" y="496" fill="#8b949e" font-size="10">High Airtime CCI Congestion</text>

  <circle cx="370" cy="492" r="5" fill="#ff1744"/>
  <text x="382" y="496" fill="#8b949e" font-size="10">WIDS Rogue AP Threat</text>

  <circle cx="530" cy="492" r="5" fill="#d500f9"/>
  <text x="542" y="496" fill="#8b949e" font-size="10">Aruba-style UXI Synthetic Probe</text>

  <line x1="720" y1="492" x2="745" y2="492" stroke="#ff3d00" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="752" y="496" fill="#ff7043" font-size="10">Sticky Client Roam Drag</text>
</svg>
"""
    )

    return "".join(svg_parts)

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
    Coordinates: viewBox 0 0 900 520.
    Wrapped in responsive HTML container to avoid clipping on wide displays.
    """
    svg_parts = []

    # HTML and SVG Header
    svg_parts.append(
        """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background-color: transparent;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .floorplan-wrapper {
    width: 100%;
    max-width: 900px;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  svg {
    width: 100%;
    height: auto;
    max-height: 525px;
    display: block;
    background-color: #0e1117;
    border-radius: 10px;
    border: 1px solid #30363d;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }
  @keyframes pulse-threat {
    0% { r: 45px; opacity: 0.6; }
    50% { r: 75px; opacity: 0.15; }
    100% { r: 45px; opacity: 0.6; }
  }
  @keyframes dash-sticky {
    to { stroke-dashoffset: -20; }
  }
  .threat-pulse { animation: pulse-threat 2s infinite ease-in-out; }
  .sticky-link { animation: dash-sticky 1s linear infinite; }
</style>
</head>
<body>
<div class="floorplan-wrapper">
<svg viewBox="0 0 900 520" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- RF Signal Gradient (Healthy) -->
    <radialGradient id="rf-healthy" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00e676" stop-opacity="0.32"/>
      <stop offset="60%" stop-color="#00e676" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#00e676" stop-opacity="0.0"/>
    </radialGradient>

    <!-- RF Signal Gradient (Congested / High Power) -->
    <radialGradient id="rf-congested" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff9100" stop-opacity="0.42"/>
      <stop offset="65%" stop-color="#ff9100" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#ff9100" stop-opacity="0.0"/>
    </radialGradient>

    <!-- Rogue AP Threat Gradient -->
    <radialGradient id="rf-threat" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff1744" stop-opacity="0.48"/>
      <stop offset="60%" stop-color="#ff1744" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#ff1744" stop-opacity="0.0"/>
    </radialGradient>

    <!-- Drop Shadows -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Blueprint Grid -->
  <g stroke="#1c2128" stroke-width="0.5">
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#161b22" stroke-width="0.8"/>
    </pattern>
    <rect width="900" height="520" fill="url(#grid)"/>
  </g>

  <!-- Campus Building Layout -->
  <!-- Outer Boundary Wall -->
  <rect x="25" y="20" width="850" height="455" rx="8" fill="#13171f" stroke="#38444d" stroke-width="2.5"/>

  <!-- Zone 1: Breakout Lounge & Cafeteria (Top Left) -->
  <rect x="25" y="20" width="285" height="205" fill="#171c26" stroke="#2d333b" stroke-width="1.5"/>
  <text x="40" y="44" fill="#8b949e" font-size="11" font-weight="600">ZONE 1: LOUNGE &amp; CAFETERIA</text>
  <text x="40" y="59" fill="#58a6ff" font-size="9.5">802.11ax Public / Guest</text>

  <!-- Zone 2: Ground Floor Lobby (Bottom Left) -->
  <rect x="25" y="225" width="285" height="250" fill="#151a24" stroke="#2d333b" stroke-width="1.5"/>
  <text x="40" y="250" fill="#8b949e" font-size="11" font-weight="600">ZONE 2: MAIN LOBBY &amp; RECEPTION</text>
  <text x="40" y="265" fill="#58a6ff" font-size="9.5">Ground Floor Entrance • High Foot-Traffic</text>

  <!-- Zone 3: Executive Conference Room B (Top Center) -->
  <rect x="310" y="20" width="280" height="205" fill="#181e2b" stroke="#388bfd" stroke-width="1.8" stroke-dasharray="4,2"/>
  <text x="325" y="44" fill="#58a6ff" font-size="11" font-weight="600">ZONE 3: EXECUTIVE CONF ROOM B</text>
  <text x="325" y="59" fill="#8b949e" font-size="9.5">Ultra HD Video Conferencing &amp; Zoom</text>

  <!-- Zone 4: Central Collaboration Atrium (Bottom Center) -->
  <rect x="310" y="225" width="280" height="250" fill="#161b24" stroke="#2d333b" stroke-width="1.5"/>
  <text x="325" y="250" fill="#8b949e" font-size="11" font-weight="600">ZONE 4: COLLABORATION ATRIUM</text>
  <text x="325" y="265" fill="#8b949e" font-size="9.5">Open Seating &amp; Hot Desks</text>

  <!-- Zone 5: Engineering & QA Lab (Right Wing) -->
  <rect x="590" y="20" width="285" height="455" fill="#171c26" stroke="#2d333b" stroke-width="1.5"/>
  <text x="605" y="44" fill="#8b949e" font-size="11" font-weight="600">ZONE 5: ENGINEERING &amp; QA LAB</text>
  <text x="605" y="59" fill="#58a6ff" font-size="9.5">High-Density Wi-Fi 6E (6GHz / 160MHz)</text>
"""
    )

    # Lookup mapping for AP positions
    ap_map: Dict[str, Dict[str, Any]] = {}

    # 2. Render RF Propagation Heatmap for Access Points
    for ap in aps:
        cx = 25 + (ap.pos_x / 100.0) * 850
        cy = 20 + (ap.pos_y / 100.0) * 455

        ap_map[ap.name] = {"x": cx, "y": cy, "ap": ap}
        ap_map[ap.ap_id] = {"x": cx, "y": cy, "ap": ap}

        # Calculate RF radius based on Tx power
        tx_pwr = max(ap.tx_power_2g_dbm, ap.tx_power_5g_dbm)
        r_coverage = 85 + (tx_pwr - 14) * 7
        is_congested = ap.channel_utilization_pct > 70.0
        grad_id = "rf-congested" if is_congested else "rf-healthy"

        # RF Propagation circles
        svg_parts.append(
            f"""
  <!-- RF Coverage: {ap.name} -->
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_coverage:.1f}" fill="url(#{grad_id})" />
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_coverage*0.5:.1f}" fill="none" stroke="{'#ff9100' if is_congested else '#00e676'}" stroke-width="1" stroke-dasharray="3,3" opacity="0.35"/>
"""
        )

    # 3. Render Rogue AP / Threats if present
    for threat in threats:
        tx = 530.0  # Placed in Conf Room B on the right side
        ty = 135.0

        svg_parts.append(
            f"""
  <!-- Rogue AP Threat: {threat.bssid} -->
  <circle cx="{tx}" cy="{ty}" r="55" class="threat-pulse" fill="url(#rf-threat)" />
  <circle cx="{tx}" cy="{ty}" r="15" fill="#b71c1c" stroke="#ff1744" stroke-width="2" filter="url(#glow)"/>
  <text x="{tx}" y="{ty+4.5}" fill="#ffffff" font-size="11" font-weight="900" text-anchor="middle">☠</text>
  <rect x="{tx-80}" y="{ty+18}" width="160" height="32" rx="4" fill="#210508" stroke="#ff1744" stroke-width="1"/>
  <text x="{tx}" y="{ty+31}" fill="#ff5252" font-size="9.5" font-weight="700" text-anchor="middle">ROGUE AP: {threat.ssid}</text>
  <text x="{tx}" y="{ty+43}" fill="#ff8a80" font-size="8.5" text-anchor="middle">{threat.bssid} ({'CONTAINED' if threat.is_contained else 'ACTIVE'})</text>
"""
        )

    # 4. Render Client Association Links (Lines from station to AP)
    for c in clients:
        cx = 25 + (c.pos_x / 100.0) * 850
        cy = 20 + (c.pos_y / 100.0) * 455

        target_ap = ap_map.get(c.ap_name)
        if target_ap:
            ap_x, ap_y = target_ap["x"], target_ap["y"]

            if c.sticky_client_detected or c.rssi_dbm < -75:
                # Sticky client: Long dashed red/orange line spanning across rooms
                mid_x = (cx + ap_x) / 2
                mid_y = (cy + ap_y) / 2
                svg_parts.append(
                    f"""
  <!-- Sticky Roaming Failure Link -->
  <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ap_x:.1f}" y2="{ap_y:.1f}" stroke="#ff3d00" stroke-width="2.5" stroke-dasharray="6,4" class="sticky-link" opacity="0.85"/>
  <rect x="{mid_x-75:.1f}" y="{mid_y-14:.1f}" width="150" height="20" rx="3" fill="#2d0f05" stroke="#ff3d00" stroke-width="1"/>
  <text x="{mid_x:.1f}" y="{mid_y:.1f}" fill="#ff7043" font-size="9" font-weight="700" text-anchor="middle">⚠️ STICKY CLIENT ({c.rssi_dbm} dBm)</text>
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
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="16" fill="#1f242e" stroke="{ap_color}" stroke-width="2.5" filter="url(#glow)"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{ap_color}"/>
  <text x="{cx:.1f}" y="{cy-22:.1f}" fill="#ffffff" font-size="11" font-weight="700" text-anchor="middle">{ap.name}</text>
  <!-- Telemetry Badge -->
  <rect x="{cx-68:.1f}" y="{cy+20:.1f}" width="136" height="30" rx="4" fill="{badge_bg}" stroke="{ap_color}" stroke-width="1"/>
  <text x="{cx:.1f}" y="{cy+33:.1f}" fill="{ap_color}" font-size="9.5" font-weight="700" text-anchor="middle">Ch {ap.channel_2g} (2.4G) | Ch {ap.channel_5g} (5G)</text>
  <text x="{cx:.1f}" y="{cy+44:.1f}" fill="#8b949e" font-size="8.5" text-anchor="middle">Airtime: {ap.channel_utilization_pct}% • {len(ap.connected_clients)} Clients</text>
"""
        )

    # 6. Render Client Station Icons & Tags
    for c in clients:
        cx = 25 + (c.pos_x / 100.0) * 850
        cy = 20 + (c.pos_y / 100.0) * 455

        is_sticky = c.sticky_client_detected or c.rssi_dbm < -75
        is_dhcp_fail = c.connection_state.value == "DHCP_FAILED"

        sta_color = "#ff3d00" if (is_sticky or is_dhcp_fail) else "#00e5ff"
        icon_symbol = "!" if is_dhcp_fail else ("⚡" if is_sticky else "💻")

        svg_parts.append(
            f"""
  <!-- Client Station: {c.hostname} -->
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="#1b2028" stroke="{sta_color}" stroke-width="1.8"/>
  <text x="{cx:.1f}" y="{cy+3:.1f}" fill="{sta_color}" font-size="8.5" text-anchor="middle">{icon_symbol}</text>
  <text x="{cx:.1f}" y="{cy-10:.1f}" fill="#e6edf3" font-size="9.5" font-weight="600" text-anchor="middle">{c.hostname}</text>
  <text x="{cx:.1f}" y="{cy+17:.1f}" fill="{sta_color}" font-size="8.5" text-anchor="middle">{c.rssi_dbm} dBm ({c.band})</text>
"""
        )

    # 7. Render UXI Sensor Probe (Placed at top right of Zone 3)
    uxi_sla = uxi_report.overall_sla if uxi_report else "PASSED"
    uxi_color = "#ff1744" if uxi_sla == "FAILED" else ("#ff9100" if uxi_sla == "DEGRADED" else "#d500f9")
    svg_parts.append(
        f"""
  <!-- Synthetic UXI Sensor Probe -->
  <g transform="translate(470, 36)">
    <rect x="0" y="0" width="112" height="34" rx="5" fill="#1b122c" stroke="{uxi_color}" stroke-width="1.2"/>
    <circle cx="12" cy="17" r="5.5" fill="{uxi_color}" filter="url(#glow)"/>
    <text x="23" y="15" fill="#e1bee7" font-size="9" font-weight="700">UXI Probe Sensor</text>
    <text x="23" y="27" fill="{uxi_color}" font-size="8.5" font-weight="600">SLA: {uxi_sla}</text>
  </g>
"""
    )

    # 8. Floorplan Legend Bar at Bottom
    svg_parts.append(
        """
  <!-- Legend Bar -->
  <rect x="25" y="482" width="850" height="26" rx="4" fill="#0d1117" stroke="#21262d" stroke-width="1"/>
  <circle cx="45" cy="495" r="4.5" fill="#00e676"/>
  <text x="56" y="499" fill="#8b949e" font-size="9.5">Clean 802.11 RF Cell</text>

  <circle cx="190" cy="495" r="4.5" fill="#ff9100"/>
  <text x="201" y="499" fill="#8b949e" font-size="9.5">High Airtime Congestion</text>

  <circle cx="370" cy="495" r="4.5" fill="#ff1744"/>
  <text x="381" y="499" fill="#8b949e" font-size="9.5">WIDS Rogue AP Threat</text>

  <circle cx="530" cy="495" r="4.5" fill="#d500f9"/>
  <text x="541" y="499" fill="#8b949e" font-size="9.5">Synthetic UXI Probe</text>

  <line x1="700" y1="495" x2="725" y2="495" stroke="#ff3d00" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="732" y="499" fill="#ff7043" font-size="9.5">Sticky Client Roam Drag</text>
</svg>
</div>
</body>
</html>
"""
    )

    return "".join(svg_parts)

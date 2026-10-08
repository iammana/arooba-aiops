#!/bin/bash
# ==============================================================================
# Arooba-AIOps: Raspberry Pi 5 Access Point Automated Installer
# Configures wlan0 as an AP with hostapd and dnsmasq while strictly preserving
# upstream internet connectivity and DNS on eth0.
# Tested on Raspberry Pi OS Bookworm (Debian 12) on Raspberry Pi 5.
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root: sudo bash setup_pi_ap.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "[+] Step 1: Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent python3-venv python3-pip iw wireless-tools

echo "[+] Step 2: Unmasking and stopping AP services during initial setup..."
systemctl unmask hostapd || true
systemctl stop hostapd || true
systemctl stop dnsmasq || true

echo "[+] Step 3: Configuring NetworkManager (preserving eth0, unmanaging wlan0)..."
if [ -d /etc/NetworkManager ]; then
  mkdir -p /etc/NetworkManager/conf.d
  cat << 'EOF' > /etc/NetworkManager/conf.d/99-unmanage-wlan0.conf
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
  # Ensure eth0 is explicitly managed by NetworkManager with auto-connect
  nmcli device set eth0 managed yes 2>/dev/null || true
  systemctl reload NetworkManager 2>/dev/null || true
fi

# Ensure eth0 link is physically up
if [ -d /sys/class/net/eth0 ]; then
  ip link set dev eth0 up 2>/dev/null || true
  nmcli device connect eth0 2>/dev/null || true
fi

echo "[+] Step 4: Setting persistent static IP on wlan0 (192.168.4.1/24) without default route..."
cat << 'EOF' > /etc/systemd/system/arooba-ap-ip.service
[Unit]
Description=Arooba AP Static IP Configuration for wlan0
Before=hostapd.service dnsmasq.service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/ip link set dev wlan0 up
ExecStart=/usr/bin/ip addr replace 192.168.4.1/24 dev wlan0
# Ensure wlan0 NEVER captures the default gateway (preserves eth0 internet uplink)
ExecStart=-/usr/bin/ip route del default dev wlan0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable arooba-ap-ip.service
systemctl restart arooba-ap-ip.service || {
  ip link set dev wlan0 up 2>/dev/null || true
  ip addr replace 192.168.4.1/24 dev wlan0 2>/dev/null || true
}
# Delete any stale default route on wlan0 immediately
ip route del default dev wlan0 2>/dev/null || true

# Optional backward compatibility with legacy ifupdown if directory exists
if [ -d /etc/network ]; then
  mkdir -p /etc/network/interfaces.d
  cat << 'EOF' > /etc/network/interfaces.d/wlan0
auto wlan0
iface wlan0 inet static
    address 192.168.4.1
    netmask 255.255.255.0
EOF
fi

echo "[+] Step 5: Configuring hostapd..."
mkdir -p /var/run/hostapd
mkdir -p /etc/hostapd
cp "${SCRIPT_DIR}/hostapd.conf.template" /etc/hostapd/hostapd.conf
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd 2>/dev/null || true

echo "[+] Step 6: Configuring dnsmasq (preventing resolvconf hijacking)..."
if [ -f /etc/dnsmasq.conf ] && [ ! -f /etc/dnsmasq.conf.orig ]; then
  mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
fi
cp "${SCRIPT_DIR}/dnsmasq.conf.template" /etc/dnsmasq.conf

# Prevent dnsmasq from modifying /etc/resolv.conf so the Pi host retains its own DNS
if [ -f /etc/default/dnsmasq ]; then
  sed -i 's|^#\?IGNORE_RESOLVCONF=.*|IGNORE_RESOLVCONF=yes|' /etc/default/dnsmasq 2>/dev/null || true
  if ! grep -q "IGNORE_RESOLVCONF=yes" /etc/default/dnsmasq 2>/dev/null; then
    echo "IGNORE_RESOLVCONF=yes" >> /etc/default/dnsmasq
  fi
fi

echo "[+] Step 7: Enabling IP forwarding & NAT routing (eth0 <-> wlan0)..."
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/90-arooba-forward.conf

# Masquerade outbound traffic over eth0
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Forwarding filter rules for Wi-Fi clients to reach internet via eth0
iptables -C FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -C FORWARD -i wlan0 -o eth0 -j ACCEPT 2>/dev/null || iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

echo "[+] Step 8: Starting AP services..."
rfkill unblock wlan || true
systemctl enable hostapd
systemctl restart hostapd
systemctl enable dnsmasq
systemctl restart dnsmasq

echo "[+] Step 9: Verifying eth0 internet uplink and DNS resolution..."
if [ -e /sys/class/net/eth0/carrier ] && [ "$(cat /sys/class/net/eth0/carrier 2>/dev/null || echo 0)" -eq 1 ]; then
  echo "  [✓] Ethernet cable detected on eth0."
  # Ensure eth0 has an IPv4 address
  if ! ip -4 addr show eth0 | grep -q "inet "; then
    echo "  [!] Acquiring DHCP lease on eth0..."
    nmcli device connect eth0 2>/dev/null || dhclient eth0 2>/dev/null || true
    sleep 2
  fi
  
  # Ensure default route points to eth0
  if ! ip route show | grep -q "^default .*dev eth0"; then
    echo "  [!] Activating default route for eth0..."
    nmcli connection up "Wired connection 1" 2>/dev/null || true
  fi
else
  echo "  [i] Note: eth0 has no active cable detected. If connected later, it will auto-configure."
fi

# Ensure DNS resolution is healthy on the host
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
  if ! python3 -c "import socket; socket.gethostbyname('dns.google')" >/dev/null 2>&1; then
    echo "  [!] Internet reachable but DNS resolution failing. Adding fallback nameservers..."
    if [ ! -L /etc/resolv.conf ]; then
      grep -q "nameserver 8.8.8.8" /etc/resolv.conf || echo "nameserver 8.8.8.8" >> /etc/resolv.conf
      grep -q "nameserver 1.1.1.1" /etc/resolv.conf || echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    fi
  else
    echo "  [✓] Pi 5 internet & DNS resolution verified."
  fi
fi

echo "[+] Step 10: Installing Python dependencies for Edge Daemon..."
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
  python3 -m venv "${PROJECT_ROOT}/.venv"
fi
"${PROJECT_ROOT}/.venv/bin/pip" install --upgrade pip
"${PROJECT_ROOT}/.venv/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"

echo "[+] Step 11: Installing and starting arooba-edge systemd service..."
sed "s|/home/pi/arooba-aiops|${PROJECT_ROOT}|g" "${PROJECT_ROOT}/edge/systemd/arooba-edge.service" > /etc/systemd/system/arooba-edge.service
systemctl daemon-reload
systemctl enable arooba-edge.service
systemctl restart arooba-edge.service

ETH0_IP=$(ip -4 addr show eth0 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1 | head -n1 || echo "")

echo "=================================================================="
echo " [SUCCESS] Raspberry Pi 5 AP is live!"
echo " SSID:     Arooba-AIOps-Lab"
echo " Password: AroobaAiOps2026!"
echo " AP IP:    192.168.4.1 (wlan0)"
if [ -n "${ETH0_IP}" ]; then
  echo " Uplink:   eth0 connected (${ETH0_IP}) - Internet Active!"
  echo " Daemon:   http://${ETH0_IP}:8000/health (Home LAN) or http://192.168.4.1:8000/health (AP)"
else
  echo " Uplink:   eth0 not currently connected. Plug in Ethernet cable anytime."
  echo " Daemon:   http://192.168.4.1:8000/health"
fi
echo "=================================================================="

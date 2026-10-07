#!/bin/bash
# ==============================================================================
# Arooba-AIOps: Raspberry Pi 5 Access Point Automated Installer
# Configures wlan0 as a 5GHz / 2.4GHz AP with hostapd, dnsmasq, and edge daemon.
# Tested on Raspberry Pi OS Bookworm (Debian 12) on Raspberry Pi 5.
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root: sudo bash setup_pi_ap.sh"
  exit 1
fi

echo "[+] Step 1: Installing dependencies..."
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent python3-venv python3-pip iw wireless-tools

echo "[+] Step 2: Unmasking and stopping services during setup..."
systemctl unmask hostapd || true
systemctl stop hostapd || true
systemctl stop dnsmasq || true

echo "[+] Step 3: Setting static IP on wlan0 (192.168.4.1/24)..."
cat << 'EOF' > /etc/network/interfaces.d/wlan0
auto wlan0
iface wlan0 inet static
    address 192.168.4.1
    netmask 255.255.255.0
EOF

ip addr add 192.168.4.1/24 dev wlan0 2>/dev/null || true

echo "[+] Step 4: Configuring hostapd..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${SCRIPT_DIR}/hostapd.conf.template" /etc/hostapd/hostapd.conf
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd 2>/dev/null || true

echo "[+] Step 5: Configuring dnsmasq..."
if [ -f /etc/dnsmasq.conf ]; then
  mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
fi
cp "${SCRIPT_DIR}/dnsmasq.conf.template" /etc/dnsmasq.conf

echo "[+] Step 6: Enabling IP forwarding & NAT (Ethernet eth0 -> wlan0)..."
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/90-arooba-forward.conf
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

echo "[+] Step 7: Starting AP services..."
rfkill unblock wlan || true
systemctl enable hostapd
systemctl restart hostapd
systemctl enable dnsmasq
systemctl restart dnsmasq

echo "[+] Step 8: Installing Python dependencies for Edge Daemon..."
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
  python3 -m venv "${PROJECT_ROOT}/.venv"
fi
"${PROJECT_ROOT}/.venv/bin/pip" install --upgrade pip
"${PROJECT_ROOT}/.venv/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"

echo "[+] Step 9: Installing arooba-edge systemd service..."
cp "${PROJECT_ROOT}/edge/systemd/arooba-edge.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable arooba-edge.service
systemctl restart arooba-edge.service

echo "=================================================================="
echo " [SUCCESS] Raspberry Pi 5 AP is live!"
echo " SSID:     Arooba-AIOps-Lab"
echo " Password: AroobaAiOps2026!"
echo " Gateway:  192.168.4.1"
echo " Daemon:   http://192.168.4.1:8000/health"
echo "=================================================================="

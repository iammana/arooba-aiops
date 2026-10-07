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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "[+] Step 1: Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent python3-venv python3-pip iw wireless-tools

echo "[+] Step 2: Unmasking and stopping services during setup..."
systemctl unmask hostapd || true
systemctl stop hostapd || true
systemctl stop dnsmasq || true

echo "[+] Step 3: Preventing NetworkManager from managing wlan0 (Bookworm compatibility)..."
if [ -d /etc/NetworkManager ]; then
  mkdir -p /etc/NetworkManager/conf.d
  cat << 'EOF' > /etc/NetworkManager/conf.d/99-unmanage-wlan0.conf
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
  systemctl reload NetworkManager 2>/dev/null || true
fi

echo "[+] Step 4: Setting persistent static IP on wlan0 (192.168.4.1/24)..."
cat << 'EOF' > /etc/systemd/system/arooba-ap-ip.service
[Unit]
Description=Arooba AP Static IP Configuration for wlan0
Before=hostapd.service dnsmasq.service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/ip link set dev wlan0 up
ExecStart=/usr/bin/ip addr replace 192.168.4.1/24 dev wlan0
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

echo "[+] Step 6: Configuring dnsmasq..."
if [ -f /etc/dnsmasq.conf ] && [ ! -f /etc/dnsmasq.conf.orig ]; then
  mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
fi
cp "${SCRIPT_DIR}/dnsmasq.conf.template" /etc/dnsmasq.conf

echo "[+] Step 7: Enabling IP forwarding & NAT (Ethernet eth0 -> wlan0)..."
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/90-arooba-forward.conf
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

echo "[+] Step 8: Starting AP services..."
rfkill unblock wlan || true
systemctl enable hostapd
systemctl restart hostapd
systemctl enable dnsmasq
systemctl restart dnsmasq

echo "[+] Step 9: Installing Python dependencies for Edge Daemon..."
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
  python3 -m venv "${PROJECT_ROOT}/.venv"
fi
"${PROJECT_ROOT}/.venv/bin/pip" install --upgrade pip
"${PROJECT_ROOT}/.venv/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt"

echo "[+] Step 10: Installing arooba-edge systemd service..."
sed "s|/home/pi/arooba-aiops|${PROJECT_ROOT}|g" "${PROJECT_ROOT}/edge/systemd/arooba-edge.service" > /etc/systemd/system/arooba-edge.service
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

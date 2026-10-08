#!/bin/bash
# ==============================================================================
# Arooba-AIOps: Raspberry Pi 5 Switch to Wi-Fi Client Mode
# Reverts AP configurations (hostapd, dnsmasq, static IP) and restores
# NetworkManager management on wlan0 so the Pi can connect to home Wi-Fi.
# Tested on Raspberry Pi OS Bookworm (Debian 12) on Raspberry Pi 5.
# ==============================================================================

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root: sudo bash switch_to_client.sh"
  exit 1
fi

echo "[+] Step 1: Stopping and disabling AP services..."
systemctl stop hostapd dnsmasq arooba-ap-ip.service arooba-edge.service 2>/dev/null || true
systemctl disable hostapd dnsmasq arooba-ap-ip.service arooba-edge.service 2>/dev/null || true

echo "[+] Step 2: Removing static AP IP configuration..."
rm -f /etc/systemd/system/arooba-ap-ip.service
rm -f /etc/network/interfaces.d/wlan0
systemctl daemon-reload

# Flush static 192.168.4.1 IP from wlan0
ip addr flush dev wlan0 2>/dev/null || true

echo "[+] Step 3: Restoring NetworkManager control over wlan0..."
if [ -f /etc/NetworkManager/conf.d/99-unmanage-wlan0.conf ]; then
  rm -f /etc/NetworkManager/conf.d/99-unmanage-wlan0.conf
fi

# Restore original dnsmasq config if backup exists
if [ -f /etc/dnsmasq.conf.orig ]; then
  mv /etc/dnsmasq.conf.orig /etc/dnsmasq.conf
fi

echo "[+] Step 4: Unblocking Wi-Fi and restarting NetworkManager..."
rfkill unblock wlan || true
systemctl restart NetworkManager

echo "[+] Step 5: Waiting for NetworkManager to initialize wlan0..."
sleep 2

echo "=================================================================="
echo " [SUCCESS] Pi 5 is back in Client Mode!"
echo " wlan0 is now managed by NetworkManager."
echo ""
echo " Connect to your home Wi-Fi using either:"
echo " 1. nmcli command:"
echo "    sudo nmcli dev wifi rescan"
echo "    sudo nmcli dev wifi connect \"YOUR_WIFI_SSID\" password \"YOUR_PASSWORD\""
echo ""
echo " 2. Interactive text UI:"
echo "    nmtui"
echo ""
echo " 3. Or using the Wi-Fi icon in the Raspberry Pi OS desktop panel."
echo "=================================================================="

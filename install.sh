#!/bin/bash
# ARASAKA FAN CONTROL - Installation Script

echo "▣ ARASAKA FAN CONTROL INSTALLER"
echo "================================"

# Install dependencies
echo "[*] Installing Python dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-tk python3-matplotlib
pip3 install --user matplotlib numpy

# Create directory structure
echo "[*] Creating directories..."
mkdir -p ~/arasaka_fan_control/profiles
mkdir -p ~/arasaka_fan_control/styles

# Install font for cyberpunk look
echo "[*] Installing Orbotron font..."
wget -q https://github.com/theleagueof/orbitron/raw/master/Orbitron%5Bwght%5D.ttf -O ~/.local/share/fonts/Orbitron.ttf
fc-cache -f

# Set permissions
echo "[*] Configuring permissions..."
sudo chmod +x arasaka_fan_control.py

# Create desktop launcher
echo "[*] Creating desktop launcher..."
cat > ~/.local/share/applications/arasaka-fan.desktop << EOF
[Desktop Entry]
Name=Arasaka Fan Control
Comment=Cyberpunk Fan Controller for Raspberry Pi 5
Exec=sudo python3 $PWD/arasaka_fan_control.py
Icon=applications-system
Terminal=false
Type=Application
Categories=System;
EOF

echo "[✓] Installation complete!"
echo "[*] Run with: sudo python3 arasaka_fan_control.py"

#!/bin/bash
# linmon installation script
# This script installs linmon for production use with systemd

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LINMON_USER="linmon"
LINMON_GROUP="linmon"
CONFIG_DIR="/etc/linmon"
STATE_DIR="/var/lib/linmon"
LOG_DIR="/var/log/linmon"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"

echo -e "${GREEN}linmon Installation Script${NC}"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Create linmon user and group
if ! id "$LINMON_USER" &>/dev/null; then
    echo "Creating user: $LINMON_USER"
    useradd --system --no-create-home --shell /bin/false "$LINMON_USER" || true
    echo -e "${GREEN}✓${NC} User created"
else
    echo -e "${YELLOW}⚠${NC} User $LINMON_USER already exists"
fi

# Add linmon user to systemd-journal group for journald access
if getent group systemd-journal >/dev/null 2>&1; then
    echo "Adding $LINMON_USER to systemd-journal group..."
    usermod -aG systemd-journal "$LINMON_USER" || true
    echo -e "${GREEN}✓${NC} Added to systemd-journal group"
else
    echo -e "${YELLOW}⚠${NC} systemd-journal group not found (non-systemd system?)"
    # Fallback: add to adm group for log file access
    if getent group adm >/dev/null 2>&1; then
        usermod -aG adm "$LINMON_USER" || true
        echo -e "${GREEN}✓${NC} Added to adm group (log file access)"
    fi
fi

# Create directories
echo "Creating directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$STATE_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR/reports"
echo -e "${GREEN}✓${NC} Directories created"

# Set permissions
echo "Setting permissions..."
chown -R "$LINMON_USER:$LINMON_GROUP" "$STATE_DIR"
chown -R "$LINMON_USER:$LINMON_GROUP" "$LOG_DIR"
chmod 755 "$CONFIG_DIR"
chmod 750 "$STATE_DIR"
chmod 750 "$LOG_DIR"
echo -e "${GREEN}✓${NC} Permissions set"

# Install configuration
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "Installing configuration..."
    if [ -f "configs/sample.yaml" ]; then
        cp configs/sample.yaml "$CONFIG_DIR/config.yaml"
        chmod 644 "$CONFIG_DIR/config.yaml"
        echo -e "${GREEN}✓${NC} Configuration installed"
        echo -e "${YELLOW}⚠${NC} Please review and edit $CONFIG_DIR/config.yaml"
    else
        echo -e "${YELLOW}⚠${NC} configs/sample.yaml not found, skipping config installation"
    fi
else
    echo -e "${YELLOW}⚠${NC} Configuration already exists at $CONFIG_DIR/config.yaml"
fi

# Install systemd service and timer
echo "Installing systemd units..."
if [ -f "systemd/linmon.service" ]; then
    cp systemd/linmon.service "$SYSTEMD_DIR/"
    chmod 644 "$SYSTEMD_DIR/linmon.service"
    echo -e "${GREEN}✓${NC} Service installed"
else
    echo -e "${RED}✗${NC} systemd/linmon.service not found"
fi

if [ -f "systemd/linmon.timer" ]; then
    cp systemd/linmon.timer "$SYSTEMD_DIR/"
    chmod 644 "$SYSTEMD_DIR/linmon.timer"
    echo -e "${GREEN}✓${NC} Timer installed"
else
    echo -e "${RED}✗${NC} systemd/linmon.timer not found"
fi

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd reloaded"

# Enable timer (but don't start it automatically)
echo ""
echo -e "${YELLOW}Note:${NC} Timer is not automatically started."
echo "To enable and start the timer, run:"
echo "  sudo systemctl enable linmon.timer"
echo "  sudo systemctl start linmon.timer"
echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review $CONFIG_DIR/config.yaml"
echo "  2. Test: sudo -u $LINMON_USER $BIN_DIR/linmon check --config $CONFIG_DIR/config.yaml"
echo "  3. Enable timer: sudo systemctl enable --now linmon.timer"

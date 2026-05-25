#!/bin/bash
# Migrate a running Client St0r install from the legacy `huduglue-*`
# systemd unit names to the current `clientst0r-*` names.
#
# WHAT THIS DOES:
#   1. Installs the new clientst0r-* unit files from deploy/
#   2. Stops + disables any huduglue-* unit files in /etc/systemd/system
#   3. Enables + starts the new clientst0r-* equivalents
#   4. Reloads systemd
#   5. Reports the new active state
#
# This is a ONE-SHOT migration. Safe to re-run (idempotent).
#
# Run from the project root:
#   sudo bash deploy/migrate-from-huduglue.sh

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Must run as root (sudo)."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY="$PROJECT_DIR/deploy"
SYSTEMD_DIR="/etc/systemd/system"

echo "═══════════════════════════════════════════════════════════"
echo " Client St0r — huduglue → clientst0r systemd unit migration"
echo "═══════════════════════════════════════════════════════════"
echo "Project:  $PROJECT_DIR"
echo ""

# Each pair: <new-clientst0r-unit> <old-huduglue-unit>
declare -A UNITS=(
    [clientst0r-gunicorn.service]=huduglue-gunicorn.service
    [clientst0r-auto-update.service]=huduglue-auto-update.service
    [clientst0r-auto-update.timer]=huduglue-auto-update.timer
    [clientst0r-breach-scan.service]=huduglue-breach-scan.service
    [clientst0r-breach-scan.timer]=huduglue-breach-scan.timer
    [clientst0r-monitor.service]=huduglue-monitor.service
    [clientst0r-monitor.timer]=huduglue-monitor.timer
    [clientst0r-psa-sync.service]=huduglue-psa-sync.service
    [clientst0r-psa-sync.timer]=huduglue-psa-sync.timer
    [clientst0r-rmm-sync.service]=huduglue-rmm-sync.service
    [clientst0r-rmm-sync.timer]=huduglue-rmm-sync.timer
)

echo "→ Installing new clientst0r-* unit files..."
for new_unit in "${!UNITS[@]}"; do
    src="$DEPLOY/$new_unit"
    dst="$SYSTEMD_DIR/$new_unit"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        chmod 0644 "$dst"
        echo "    installed $new_unit"
    else
        echo "    (skip) $new_unit not found in $DEPLOY"
    fi
done

systemctl daemon-reload

echo ""
echo "→ Stopping + disabling legacy huduglue-* units..."
for new_unit in "${!UNITS[@]}"; do
    old_unit="${UNITS[$new_unit]}"
    if systemctl list-unit-files "$old_unit" --no-legend 2>/dev/null | grep -q .; then
        echo "    handling $old_unit"
        systemctl stop "$old_unit" 2>/dev/null || true
        systemctl disable "$old_unit" 2>/dev/null || true
        rm -f "$SYSTEMD_DIR/$old_unit"
    fi
done
# Clean up the gunicorn backup if it lingers
rm -f "$SYSTEMD_DIR/huduglue-gunicorn.service.backup"

systemctl daemon-reload

echo ""
echo "→ Enabling + starting clientst0r-* units..."
# gunicorn first (the web app), then timers, then their backing services
ENABLE_ORDER=(
    clientst0r-gunicorn.service
    clientst0r-auto-update.timer
    clientst0r-breach-scan.timer
    clientst0r-monitor.timer
    clientst0r-psa-sync.timer
    clientst0r-rmm-sync.timer
)
for unit in "${ENABLE_ORDER[@]}"; do
    if [ -f "$SYSTEMD_DIR/$unit" ]; then
        systemctl enable "$unit" 2>&1 | sed 's/^/    /'
        systemctl restart "$unit" 2>&1 | sed 's/^/    /' || true
    fi
done

systemctl daemon-reload

echo ""
echo "→ Active units after migration:"
systemctl list-units --type=service,timer --no-legend --no-pager 'clientst0r-*' 2>&1 | sed 's/^/    /'

echo ""
echo "✓ Migration complete."
echo "  Smoke test:  curl -fsSL http://localhost:8000/health/"

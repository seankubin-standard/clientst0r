#!/bin/bash
# Client St0r Update Instructions
# Downloaded and executed by perform_update() — do not rename or move
#
# Environment variables (passed by caller):
#   CLIENTST0R_BASE_DIR      - absolute path to the project root
#   CLIENTST0R_SERVICE_NAME  - systemd service name (or empty if none)

set -euo pipefail

# Ensure standard system utilities are available regardless of the calling
# process's PATH (gunicorn restricts PATH to venv/bin via EnvironmentFile)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

BASE_DIR="${CLIENTST0R_BASE_DIR:-$(dirname "$(realpath "$0")")/..}"
SERVICE="${CLIENTST0R_SERVICE_NAME:-}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

# Trap: log exactly which command failed and on which line
trap 'log "ERROR: command failed at line $LINENO: $BASH_COMMAND (exit $?)"' ERR

log "=================================================="
log "Client St0r Update Instructions"
log "=================================================="
log "Base directory: $BASE_DIR"
log "Service: ${SERVICE:-<none detected>}"

# --- Resolve git binary (path varies by OS / install method) ---
GIT=$(command -v git 2>/dev/null || true)
if [ -z "$GIT" ]; then
    log "ERROR: git not found in PATH. Please install git."
    exit 1
fi
log "Using git: $GIT"

# --- Venv detection (checks common names and locations) ---
VENV_DIR=""
for candidate in \
    "$BASE_DIR/venv" \
    "$BASE_DIR/.venv" \
    "$BASE_DIR/env" \
    "$BASE_DIR/clientst0r/venv" \
    "$BASE_DIR/clientst0r/.venv" \
    "$(dirname "$BASE_DIR")/venv" \
    "$(dirname "$BASE_DIR")/.venv"; do
    if [ -f "$candidate/bin/python" ]; then
        VENV_DIR="$candidate"
        break
    fi
done

if [ -z "$VENV_DIR" ]; then
    VENV_DIR=$(find "$BASE_DIR" -maxdepth 2 -type d \( -name "venv" -o -name ".venv" -o -name "env" \) 2>/dev/null | head -1 || true)
fi

if [ -z "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
    log "ERROR: Virtual environment not found. Searched in $BASE_DIR and parent."
    exit 1
fi

log "Using virtual environment: $VENV_DIR"

# --- Service detection (if not provided by caller) ---
if [ -z "$SERVICE" ]; then
    for svc in clientst0r-gunicorn.service huduglue-gunicorn.service itdocs-gunicorn.service; do
        if /usr/bin/systemctl is-active "$svc" >/dev/null 2>&1; then
            SERVICE="$svc"
            break
        fi
    done
fi

# =====================================================================
# Step 1: Git fetch + reset
# =====================================================================
log ""
log "Step 1/5: Fetching latest code from GitHub..."
$GIT -C "$BASE_DIR" fetch origin main
$GIT -C "$BASE_DIR" reset --hard origin/main

NEW_VERSION=$(grep "VERSION = " "$BASE_DIR/config/version.py" 2>/dev/null | cut -d"'" -f2 || echo "unknown")
log "Step 1/5: Code updated. New version: $NEW_VERSION"

# =====================================================================
# Step 2: Install Python dependencies
# =====================================================================
log ""
log "Step 2/5: Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$BASE_DIR/requirements.txt"
log "Step 2/5: Core dependencies installed"

# Optional requirements (non-critical)
for req_file in requirements-graphql.txt requirements-optional.txt; do
    if [ -f "$BASE_DIR/$req_file" ]; then
        log "Installing optional: $req_file"
        ( "$VENV_DIR/bin/pip" install -q -r "$BASE_DIR/$req_file" ) \
            || log "[WARN] Optional $req_file install failed (non-critical)"
    fi
done

# =====================================================================
# Step 3: Database migrations
# =====================================================================
log ""
log "Step 3/5: Running database migrations..."
"$VENV_DIR/bin/python" "$BASE_DIR/manage.py" migrate --noinput
log "Step 3/5: Migrations completed"

# =====================================================================
# Step 4: Collect static files
# =====================================================================
log ""
log "Step 4/5: Collecting static files..."
"$VENV_DIR/bin/python" "$BASE_DIR/manage.py" collectstatic --noinput
log "Step 4/5: Static files collected"

# =====================================================================
# Optional extras (non-critical — failures are logged but do not abort)
# =====================================================================
log ""
log "Running optional update steps..."

# Gunicorn environment fix
FIX_SCRIPT="$BASE_DIR/scripts/fix_gunicorn_env.sh"
if [ -f "$FIX_SCRIPT" ]; then
    log "Applying gunicorn environment fix..."
    ( chmod +x "$FIX_SCRIPT" && "$FIX_SCRIPT" ) \
        || log "[WARN] Gunicorn env fix failed (non-critical)"
fi

# Mobile build setup
MOBILE_SETUP="$BASE_DIR/deploy/setup_mobile_build.sh"
if [ -f "$MOBILE_SETUP" ]; then
    log "Running mobile build setup..."
    ( chmod +x "$MOBILE_SETUP" && "$MOBILE_SETUP" ) \
        || log "[WARN] Mobile build setup failed (non-critical)"
fi

# Diagram previews
( "$VENV_DIR/bin/python" "$BASE_DIR/manage.py" generate_diagram_previews --force 2>&1 \
    && log "Diagram previews generated" ) \
    || log "[WARN] Diagram preview generation failed (non-critical)"

# Workflow diagrams
( "$VENV_DIR/bin/python" "$BASE_DIR/manage.py" generate_workflow_diagrams 2>&1 \
    && log "Workflow diagrams generated" ) \
    || log "[WARN] Workflow diagram generation failed (non-critical)"

# fail2ban sudoers (install if fail2ban present and sudoers not yet configured)
if command -v fail2ban-client >/dev/null 2>&1; then
    FB_SRC="$BASE_DIR/deploy/clientst0r-fail2ban-sudoers"
    FB_DEST="/etc/sudoers.d/clientst0r-fail2ban"
    if [ -f "$FB_SRC" ] && [ ! -f "$FB_DEST" ]; then
        log "Installing fail2ban sudoers configuration..."
        ( sudo /usr/bin/cp "$FB_SRC" "$FB_DEST" && sudo /usr/bin/chmod 0440 "$FB_DEST" \
            && log "fail2ban sudoers installed" ) \
            || log "[WARN] fail2ban sudoers install failed (non-critical)"
    else
        log "fail2ban sudoers already configured"
    fi
fi

# Cron job for web GUI updates (one-time setup)
CRON_JOB="* * * * * $BASE_DIR/scripts/check_update_trigger.sh"
if ! crontab -l 2>/dev/null | grep -q "check_update_trigger.sh"; then
    ( (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - \
        && log "Cron job configured for web GUI updates" ) \
        || log "[WARN] Cron job setup failed (non-critical)"
fi

# =====================================================================
# Step 5: Clear Python bytecode cache + hard restart
# =====================================================================
log ""
log "Step 5/5: Clearing bytecode cache and restarting service..."

# Purge __pycache__ and .pyc files so no stale bytecode survives the update.
# (git reset updates mtime but this is belt-and-suspenders for edge cases.)
find "$BASE_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$BASE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
log "Bytecode cache cleared"

SYSTEMD_RUN=$(command -v systemd-run 2>/dev/null || true)
SYSTEMCTL=$(command -v systemctl 2>/dev/null || true)

if [ -n "$SERVICE" ] && [ -n "$SYSTEMCTL" ]; then
    # Hard restart: stop the service, pkill -9 any orphaned workers that didn't
    # respond to SIGTERM, then start fresh.  This is the same strategy used by
    # the web UI "Force Restart" button and is the only reliable way to ensure
    # every worker is on the new code when a previous restart was partial.
    RESTART_SCHEDULED=0

    if [ -n "$SYSTEMD_RUN" ]; then
        HARD_RESTART_CMD="$SYSTEMCTL stop $SERVICE; /usr/bin/pkill -9 -f gunicorn 2>/dev/null || true; sleep 1; $SYSTEMCTL start $SERVICE"
        if sudo "$SYSTEMD_RUN" --on-active=5 --system /bin/bash -c "$HARD_RESTART_CMD" 2>/dev/null; then
            log "Step 5/5: Hard restart of '$SERVICE' scheduled via systemd-run (5-second delay)"
            RESTART_SCHEDULED=1
        else
            log "[WARN] systemd-run failed — falling back to nohup"
        fi
    fi

    if [ "$RESTART_SCHEDULED" -eq 0 ]; then
        nohup sudo /bin/bash -c "sleep 5; $SYSTEMCTL stop $SERVICE; /usr/bin/pkill -9 -f gunicorn 2>/dev/null || true; sleep 1; $SYSTEMCTL start $SERVICE" >/dev/null 2>&1 &
        disown 2>/dev/null || true
        log "Step 5/5: Hard restart of '$SERVICE' scheduled via nohup (5-second delay)"
    fi
else
    # No systemd service — kill all gunicorn workers then restart master
    nohup sudo /bin/bash -c "sleep 5 && pkill -9 -f gunicorn 2>/dev/null || true" >/dev/null 2>&1 &
    disown 2>/dev/null || true
    log "Step 5/5: Gunicorn hard-kill scheduled via nohup (5-second delay)"
fi

log ""
log "=================================================="
log "Update complete! Please wait 10 seconds then refresh."
log "=================================================="

exit 0

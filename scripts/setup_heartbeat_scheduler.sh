#!/usr/bin/env bash
# setup_heartbeat_scheduler.sh — Install VitaClaw heartbeat as a periodic job.
#
# macOS: installs a launchd user agent (runs every 2 hours)
# Linux: installs a crontab entry (runs every 2 hours)
#
# Usage:
#   bash scripts/setup_heartbeat_scheduler.sh          # install
#   bash scripts/setup_heartbeat_scheduler.sh remove    # uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VITACLAW_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LABEL="com.vitaclaw.heartbeat"
PYTHON="${PYTHON:-python3}"
ACTION="${1:-install}"

# ---------- macOS (launchd) ----------
install_macos() {
    local plist_src="$VITACLAW_ROOT/configs/$LABEL.plist"
    local plist_dst="$HOME/Library/LaunchAgents/$LABEL.plist"

    mkdir -p "$HOME/Library/LaunchAgents"
    mkdir -p "$VITACLAW_ROOT/logs"

    # Replace placeholder with actual path
    sed "s|__VITACLAW_ROOT__|$VITACLAW_ROOT|g" "$plist_src" > "$plist_dst"

    # Also set the correct python path
    local python_path
    python_path="$(command -v "$PYTHON")"
    sed -i '' "s|/usr/bin/env</string>|$python_path</string>|" "$plist_dst"
    # Remove the env wrapper — use python path directly
    sed -i '' '/<string>python3<\/string>/d' "$plist_dst"

    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$plist_dst"

    echo "[+] Installed launchd agent: $plist_dst"
    echo "    Heartbeat runs every 2 hours."
    echo "    Logs: $VITACLAW_ROOT/logs/heartbeat.log"
    echo ""
    echo "    To check status:  launchctl print gui/$(id -u)/$LABEL"
    echo "    To run now:       launchctl kickstart gui/$(id -u)/$LABEL"
    echo "    To remove:        bash $0 remove"
}

remove_macos() {
    local plist_dst="$HOME/Library/LaunchAgents/$LABEL.plist"
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    rm -f "$plist_dst"
    echo "[x] Removed launchd agent: $LABEL"
}

# ---------- Linux (cron) ----------
CRON_MARKER="# vitaclaw-heartbeat"

install_linux() {
    local python_path
    python_path="$(command -v "$PYTHON")"
    local cron_line="0 */2 * * * cd $VITACLAW_ROOT && $python_path scripts/run_health_heartbeat.py >> logs/heartbeat.log 2>&1 $CRON_MARKER"

    mkdir -p "$VITACLAW_ROOT/logs"

    # Remove old entry if present, then add
    (crontab -l 2>/dev/null | grep -v "$CRON_MARKER"; echo "$cron_line") | crontab -

    echo "[+] Installed cron job (every 2 hours)."
    echo "    Logs: $VITACLAW_ROOT/logs/heartbeat.log"
    echo "    To remove: bash $0 remove"
}

remove_linux() {
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab -
    echo "[x] Removed cron entry: vitaclaw-heartbeat"
}

# ---------- Dispatch ----------
case "$(uname -s)" in
    Darwin)
        if [ "$ACTION" = "remove" ]; then remove_macos; else install_macos; fi
        ;;
    Linux)
        if [ "$ACTION" = "remove" ]; then remove_linux; else install_linux; fi
        ;;
    *)
        echo "[-] Unsupported platform: $(uname -s). Please set up a cron job manually:"
        echo "    0 */2 * * * cd $VITACLAW_ROOT && $PYTHON scripts/run_health_heartbeat.py"
        exit 1
        ;;
esac

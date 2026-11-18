#!/bin/bash
# Installs (or restarts) the CloudTabs Relay server as a login item.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="io.github.cloudtabs-relay"
APP_DIR="$HOME/Library/Application Support/CloudTabs Relay"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PORT=47823

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "python3 not found. Run: xcode-select --install"; exit 1
fi
REAL_PY="$("$PY" -c 'import os,sys; print(os.path.realpath(sys.executable))')"

mkdir -p "$APP_DIR" "$HOME/Library/LaunchAgents"
cp "$DIR/server/cloudtabs_relay.py" "$APP_DIR/"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$REAL_PY</string>
    <string>$APP_DIR/cloudtabs_relay.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$APP_DIR/server.log</string>
  <key>StandardErrorPath</key><string>$APP_DIR/server.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

# Wait for the server to answer.
for _ in $(seq 1 20); do
  curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
  sleep 0.3
done

RESULT="$(curl -s "http://127.0.0.1:$PORT/tabs" || echo '{"error":"down"}')"
BINARY="$(curl -s "http://127.0.0.1:$PORT/health" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("binary",""))' 2>/dev/null || true)"

if echo "$RESULT" | grep -q '"error": "permission"'; then
  echo ""
  echo "⚠️  The server is running but needs Full Disk Access."
  echo ""
  echo "   1. System Settings opens on the right page."
  echo "   2. Click « + », press Cmd+Shift+G and paste this path:"
  echo ""
  echo "      $BINARY"
  echo ""
  echo "   3. Turn it on, then run ./install.sh again."
  echo ""
  echo -n "$BINARY" | pbcopy && echo "   (path copied to the clipboard)"
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
elif echo "$RESULT" | grep -q '"devices"'; then
  COUNT="$(echo "$RESULT" | "$PY" -c 'import json,sys; d=json.load(sys.stdin); print(sum(len(x["tabs"]) for x in d["devices"]))')"
  echo "✅ All good: $COUNT iCloud tab(s) found."
  echo "   Now load the « extension » folder in your browser (see README)."
else
  echo "Server response: $RESULT"
  echo "Log: $APP_DIR/server.log"
fi

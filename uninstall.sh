#!/bin/bash
# Stops and removes the CloudTabs Relay server.
LABEL="io.github.cloudtabs-relay"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/Library/Application Support/CloudTabs Relay"
echo "Server removed. Also remove the extension from your browser and the Python entry from Full Disk Access."

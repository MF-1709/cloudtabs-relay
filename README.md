# CloudTabs Relay

**Open your iPhone's Safari tabs in Dia, Chrome, Arc or any Chromium browser on your Mac.**
No copy-paste, nothing to install on the iPhone, no Apple developer account.

```
iPhone (Safari) ──iCloud Tabs──▶ Mac: CloudTabs.db ──▶ local relay ──▶ browser extension
```

Safari already syncs your open tabs to iCloud, and macOS keeps a local copy of them in `CloudTabs.db`, even if you never open Safari on your Mac.
CloudTabs Relay is a tiny local server that reads that copy, plus an extension that shows the list and opens tabs in one click.

## Features
- Badge with the number of tabs open on your iPhone/iPad
- Tabs grouped by device, with favicons
- Click to open, ⌘-click to open in the background, “Open all” per device
- Instant filter (Enter opens the first match)
- Live refresh: every 3 s while the popup is open, every 30 s for the badge
- English & French UI

## Requirements
- macOS with `python3` (`xcode-select --install` if missing)
- **Safari turned on in iCloud** on both the iPhone *and* the Mac:
  Settings › [your name] › iCloud › Safari
- A Chromium-based browser: Dia, Chrome, Arc, Brave, Edge…

## Install

**1. The relay**
```bash
git clone https://github.com/MF-1709/cloudtabs-relay.git
cd cloudtabs-relay
./install.sh
```
The first run tells you that **Full Disk Access** is missing. This is expected: macOS protects Safari's folder.
The script opens the right System Settings page and copies the Python binary path to your clipboard.
Click **+**, press **⌘⇧G**, paste the path, turn it on, then run `./install.sh` again. It should print ✅.
If the settings page doesn’t open, go to **System Settings › Privacy & Security › Full Disk Access** manually. If macOS still refuses access when using the Python bundled with Xcode, put a standalone Python 3 first on `PATH`, then run the installer and grant access to that Python.

**2. The extension**
1. Open `chrome://extensions` in your browser.
2. Turn on **Developer mode**.
3. Click **Load unpacked** and pick the `extension` folder.
4. Pin the icon.

## How it works
- The relay runs as a LaunchAgent: it starts at login and restarts itself if it crashes.
- It listens on `127.0.0.1:47823`. The API has no authentication, so other local programs can also read the synced tab titles and URLs.
- It's **read-only**. It copies `CloudTabs.db` to a temp folder, reads it there and deletes the copy, so Safari's database is never locked or modified.
- The result is cached in memory and only re-read when the database changes.
- Footprint: about 15–20 MB of RAM, no CPU while idle, a few milliseconds per request.

### Why a local server?
An extension can't read files on your Mac, and Apple offers no web API for iCloud Tabs.
Letting the browser launch a helper on demand (native messaging) would make macOS attribute the file access to the browser itself. You'd then have to give your **browser** Full Disk Access, which is a bad idea.
A separate relay lets you grant Full Disk Access to the Python interpreter used by the relay. The permission also applies to other scripts that run through that interpreter.

## Limitations
- **Latency**: you depend on iCloud sync, usually a few seconds to a few minutes.
  If the list looks stale, opening Safari on the Mac once forces a sync.
- **One-way**: tabs can't be closed on the iPhone from here.
  Tip: iPhone Settings › Safari › Close Tabs › After One Day/Week.
- `CloudTabs.db` is an undocumented Apple format. A future macOS update may change it.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Red `!` badge, “local server isn't responding” | Run `./install.sh` |
| “Full Disk Access is missing” | Add the path shown in the popup to System Settings › Privacy & Security › Full Disk Access, then run `./install.sh` |
| “CloudTabs.db not found” | Turn on Safari in iCloud settings on the Mac |
| Logs | `~/Library/Application Support/CloudTabs Relay/server.log` |

## Uninstall
```bash
./uninstall.sh
```
Then remove the extension, and the Python entry from Full Disk Access.

## License
MIT. Not affiliated with Apple. Safari and iCloud are trademarks of Apple Inc.

#!/usr/bin/env python3
"""CloudTabs Relay — local server.

Reads the iCloud Tabs (Safari on iPhone/iPad) that macOS stores in CloudTabs.db
and serves them as JSON on http://127.0.0.1:47823 for the browser extension.
Read-only: it never writes to Safari's database.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

__version__ = "1.0.0"

HOST = "127.0.0.1"
PORT = int(os.environ.get("CLOUDTABS_RELAY_PORT", "47823"))

CANDIDATES = [
    os.path.expanduser("~/Library/Containers/com.apple.Safari/Data/Library/Safari/CloudTabs.db"),
    os.path.expanduser("~/Library/Safari/CloudTabs.db"),
]
if os.environ.get("CLOUDTABS_RELAY_DB"):
    CANDIDATES.insert(0, os.environ["CLOUDTABS_RELAY_DB"])

QUERY = """
SELECT d.device_uuid, d.device_name, t.title, t.url
FROM cloud_tabs t
JOIN cloud_tab_devices d ON t.device_uuid = d.device_uuid
"""


def running_binary():
    """Real path of the running binary: this is what needs Full Disk Access."""
    try:
        out = subprocess.run(["ps", "-o", "comm=", "-p", str(os.getpid())],
                             capture_output=True, text=True, timeout=2).stdout.strip()
        if out.startswith("/"):
            return os.path.realpath(out)
    except Exception:
        pass
    return os.path.realpath(sys.executable)


def find_db():
    for path in CANDIDATES:
        try:
            os.stat(path)
            return path
        except PermissionError:
            raise
        except FileNotFoundError:
            continue
    return None


_cache = {"sig": None, "data": None}


def signature(db):
    sig = []
    for suffix in ("", "-wal", "-shm"):
        try:
            st = os.stat(db + suffix)
            sig.append((suffix, st.st_mtime_ns, st.st_size))
        except FileNotFoundError:
            pass
    return tuple(sig)


def read_tabs():
    db = find_db()
    if db is None:
        return {"error": "notfound",
                "message": "CloudTabs.db not found. Turn on Safari in iCloud settings on this Mac."}

    sig = signature(db)
    if sig == _cache["sig"] and _cache["data"] is not None:
        return _cache["data"]

    # Work on a copy (with its WAL journal) so Safari's database is never locked.
    tmp = tempfile.mkdtemp(prefix="cloudtabs-relay-")
    try:
        copy = os.path.join(tmp, "CloudTabs.db")
        for suffix in ("", "-wal", "-shm"):
            if os.path.exists(db + suffix):
                shutil.copy2(db + suffix, copy + suffix)
        con = sqlite3.connect(copy)
        try:
            rows = con.execute(QUERY).fetchall()
        finally:
            con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    devices = {}
    for uuid, name, title, url in rows:
        if not url:
            continue
        dev = devices.setdefault(uuid, {"id": uuid, "name": name or "Device", "tabs": []})
        dev["tabs"].append({"title": title or url, "url": url})

    # iPhones first, then everything else by name.
    ordered = sorted(devices.values(),
                     key=lambda d: (0 if "iphone" in d["name"].lower() else 1, d["name"].lower()))
    data = {"devices": ordered, "updated": time.time()}
    _cache.update(sig=sig, data=data)
    return data


class Handler(BaseHTTPRequestHandler):
    server_version = f"CloudTabsRelay/{__version__}"

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Localhost only (blocks DNS rebinding) and extensions only (web pages can't query it).
        if self.headers.get("Host") not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}"):
            return self._send(403, {"error": "forbidden"})
        origin = self.headers.get("Origin")
        if origin and not origin.startswith(("chrome-extension://", "moz-extension://")):
            return self._send(403, {"error": "forbidden"})

        if self.path == "/health":
            return self._send(200, {"ok": True, "version": __version__, "binary": running_binary()})
        if self.path == "/tabs":
            try:
                return self._send(200, read_tabs())
            except PermissionError:
                return self._send(200, {
                    "error": "permission",
                    "message": "Full Disk Access is missing.",
                    "binary": running_binary(),
                })
            except Exception as exc:  # database mid-write, unexpected schema…
                return self._send(200, {"error": "read", "message": str(exc)})
        return self._send(404, {"error": "notfound"})

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CloudTabs Relay {__version__} on http://{HOST}:{PORT} (binary: {running_binary()})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

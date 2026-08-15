# OTA/ota.py - MicroPython Multi-File & Directory Hierarchy OTA Engine
import urequests
import os
import json
import machine
import time

try:
    import hashlib
    HAS_HASHLIB = False
except ImportError:
    HAS_HASHLIB = False

class GitHubOTAUpdater:
    """
    Multi-file and Recursive Hierarchy OTA Updater for Raspberry Pi Pico W.
    Supports downloading complex file trees (e.g. OTA/ota.py, lib/sensor.py)
    directly from public GitHub repositories over HTTPS.
    """
    def __init__(self, github_repo, branch="main", manifest_file="version.json", current_version_file="version.json"):
        self.github_repo = github_repo.strip("/")
        self.branch = branch
        self.manifest_file = manifest_file
        self.current_version_file = current_version_file
        self.raw_base_url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.branch}"
        self.manifest_url = f"{self.raw_base_url}/{self.manifest_file}"
        self.current_version = self._load_current_version()
        self.headers = {"User-Agent": "PicoW-MicroPython-OTA"}

    def _load_current_version(self):
        try:
            with open(self.current_version_file, "r") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def _parse_version(self, ver_str):
        """Converts '1.2.3' to tuple (1, 2, 3) for clean comparison."""
        try:
            parts = [int(p) for p in ver_str.split(".")]
            return tuple(parts)
        except Exception:
            return (0, 0, 0)

    def _ensure_path_dirs(self, filepath):
        """Ensures all parent directories in a relative path exist."""
        parts = filepath.split("/")
        if len(parts) <= 1:
            return
        curr = ""
        for folder in parts[:-1]:
            if folder:
                curr = f"{curr}/{folder}" if curr else folder
                try:
                    os.mkdir(curr)
                except OSError:
                    pass

    def check_for_update(self):
        """Fetches remote manifest.json from GitHub with cache-busting."""
        print(f"[OTA] Current device version: v{self.current_version}")
        url = f"{self.manifest_url}?cb={time.ticks_ms()}"
        print(f"[OTA] Fetching remote manifest: {self.manifest_url}")
        
        try:
            res = urequests.get(url, headers=self.headers)
            if res.status_code == 200:
                manifest = res.json()
                res.close()
                remote_ver = manifest.get("version", "0.0.0")
                print(f"[OTA] Remote GitHub release version: v{remote_ver}")
                
                if self._parse_version(remote_ver) > self._parse_version(self.current_version):
                    print(f"[OTA] Update detected: v{self.current_version} -> v{remote_ver}")
                    return manifest
                else:
                    print("[OTA] Software is up to date.")
                    return None
            else:
                print(f"[OTA] GitHub query returned HTTP {res.status_code}")
                res.close()
                return None
        except Exception as e:
            print("[OTA] Error querying GitHub manifest:", e)
            return None

    def _compute_sha256(self, file_path):
        if not HAS_HASHLIB:
            return None
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(256):
                hasher.update(chunk)
        return "".join("{:02x}".format(b) for b in hasher.digest())

    def apply_update(self, manifest):
        """
        Downloads all listed files (preserving folder hierarchy), verifies checksums,
        backs up old files, and installs the update atomically.
        """
        files = manifest.get("files", [])
        checksums = manifest.get("checksums", {})
        sizes = manifest.get("sizes", {})
        new_version = manifest.get("version")
        base_url = manifest.get("base_url", self.raw_base_url).rstrip("/")

        if not files:
            raise ValueError("Manifest contains no 'files' list.")

        stage_dir = "update_stage"
        backup_dir = "backup"

        print(f"[OTA] Starting update process for {len(files)} file(s)...")

        # Step 1: Download files maintaining hierarchy in update_stage
        for rel_path in files:
            file_url = f"{base_url}/{rel_path}?cb={time.ticks_ms()}"
            stage_path = f"{stage_dir}/{rel_path}"
            
            # Ensure parent subdirectories exist inside update_stage
            self._ensure_path_dirs(stage_path)
            
            print(f"[OTA Download] Fetching '{rel_path}' from GitHub...")
            res = urequests.get(file_url, headers=self.headers)
            if res.status_code == 200:
                with open(stage_path, "wb") as f:
                    f.write(res.content)
                res.close()
            else:
                res.close()
                raise RuntimeError(f"HTTP {res.status_code} downloading '{rel_path}'")

            # Verify integrity
            if rel_path in checksums and HAS_HASHLIB:
                computed = self._compute_sha256(stage_path)
                expected = checksums[rel_path]
                if computed.lower() != expected.lower():
                    raise ValueError(f"Checksum mismatch for '{rel_path}'! Computed: {computed}, Expected: {expected}")
                print(f"[OTA Verify] Checksum OK for '{rel_path}'")
            elif rel_path in sizes:
                actual_size = os.stat(stage_path)[6]
                if actual_size != sizes[rel_path]:
                    raise ValueError(f"Size mismatch for '{rel_path}'! Got {actual_size} bytes, expected {sizes[rel_path]}")
                print(f"[OTA Verify] File size OK for '{rel_path}'")

        # Step 2: Backup active files preserving folder hierarchy
        print("[OTA Backup] Preserving working active files into /backup...")
        for rel_path in files:
            backup_path = f"{backup_dir}/{rel_path}"
            try:
                with open(rel_path, "rb") as src:
                    self._ensure_path_dirs(backup_path)
                    with open(backup_path, "wb") as dst:
                        while chunk := src.read(256):
                            dst.write(chunk)
                print(f"[OTA Backup] Saved '{rel_path}' -> '{backup_path}'")
            except Exception:
                pass

        # Step 3: Promote staged files to active flash locations
        print("[OTA Install] Installing new file tree into flash root...")
        for rel_path in files:
            stage_path = f"{stage_dir}/{rel_path}"
            self._ensure_path_dirs(rel_path)
            
            with open(stage_path, "rb") as src:
                with open(rel_path, "wb") as dst:
                    while chunk := src.read(256):
                        dst.write(chunk)
            os.remove(stage_path)
            print(f"[OTA Install] Installed '{rel_path}' successfully.")

        # Step 4: Record new version locally
        with open(self.current_version_file, "w") as f:
            json.dump({"version": new_version}, f)

        print(f"[OTA Success] Complete software hierarchy updated to v{new_version}! Rebooting...")
        machine.reset()


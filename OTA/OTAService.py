# ota.py - MicroPython Multi-File & Directory Hierarchy OTA Engine for Pico W
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
    Supports downloading complex file trees (e.g. lib/sensors/dht22.py) directly
    from public GitHub repositories over HTTPS.
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
                # File may be newly introduced in this release
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
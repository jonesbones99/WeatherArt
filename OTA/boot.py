# boot.py - Executed on MicroPython startup before main.py
import os
import machine
CRASH_COUNTER_FILE = "crash_count.txt"
MAX_CRASHES = 3
def read_crash_count():
    try:
        with open(CRASH_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def write_crash_count(count):
    try:
        with open(CRASH_COUNTER_FILE, "w") as f:
            f.write(str(count))
    except Exception:
        pass

def is_dir(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False

def ensure_path_dirs(filepath):
    """Creates parent directory tree for a file path if it doesn't exist."""
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

def restore_directory_recursive(src_dir, dst_dir=""):
    """Recursively copies all files and subdirectories from src_dir to dst_dir."""
    try:
        items = os.listdir(src_dir)
    except OSError:
        return
    for item in items:
        src_path = f"{src_dir}/{item}"
        dst_path = f"{dst_dir}/{item}" if dst_dir else item
        
        if is_dir(src_path):
            ensure_path_dirs(f"{dst_path}/dummy.txt")
            restore_directory_recursive(src_path, dst_path)
        else:
            ensure_path_dirs(dst_path)
            try:
                with open(src_path, "rb") as s, open(dst_path, "wb") as d:
                    while chunk := s.read(256):
                        d.write(chunk)
                print(f"[BOOT Rollback] Restored: {dst_path}")
            except Exception as e:
                print(f"[BOOT Rollback Error] Failed to restore {dst_path}: {e}")

def rollback_backup():
    print("[BOOT] Consecutive failure threshold reached. Initiating full recursive rollback...")
    try:
        if is_dir("backup"):
            restore_directory_recursive("backup", dst_dir="")
            print("[BOOT] Recursive rollback complete! Preserved file hierarchy restored.")
        else:
            print("[BOOT] No /backup directory found to restore!")
    except Exception as e:
        print(f"[BOOT] Rollback failed: {e}")
        
# Increment crash counter on boot
crashes = read_crash_count() + 1
write_crash_count(crashes)
if crashes > MAX_CRASHES:
    print(f"[BOOT] WARNING: Detected {crashes} consecutive failed boot attempts!")
    rollback_backup()
    # Reset count after rollback attempt
    write_crash_count(0)
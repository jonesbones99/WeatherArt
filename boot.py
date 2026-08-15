# boot.py (Root MicroPython boot launcher)
try:
    import OTA.boot
except Exception as e:
    print("[BOOT LAUNCHER ERROR] Failed to load OTA/boot.py:", e)
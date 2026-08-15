# Server.py - Wi-Fi Manager & Connection Class for Raspberry Pi Pico W
import network
import time
class Server:
    """
    Manages Wi-Fi connections on the Raspberry Pi Pico W using credentials 
    loaded from config.txt (Line 1: Password, Line 2: SSID).
    """
    def __init__(self, config_file="config.txt", max_attempts=15):
        self.config_file = config_file
        self.max_attempts = max_attempts
        self.wlan = network.WLAN(network.STA_IF)
        self.ssid, self.password = self.load_wifi_credentials()
        
    def load_wifi_credentials(self):
        """
        Reads Wi-Fi credentials from config.txt.
        Line 1: Password:your_password
        Line 2: SSID:your_ssid
        """
        ssid = None
        password = None
        try:
            with open(self.config_file, "r") as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key_clean = key.strip().lower()
                    val_clean = val.strip()
                    if key_clean == "password":
                        password = val_clean
                    elif key_clean == "ssid":
                        ssid = val_clean
            # Fallback by line index (Line 1 = Password, Line 2 = SSID)
            clean_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
            if len(clean_lines) >= 2:
                if not password:
                    password = clean_lines[0].split(":", 1)[-1].strip()
                if not ssid:
                    ssid = clean_lines[1].split(":", 1)[-1].strip()
        except Exception as e:
            print(f"[SERVER CONFIG ERROR] Could not read '{self.config_file}': {e}")
        return ssid, password

    def connect(self):
        """Activates WLAN interface and attempts Wi-Fi connection."""
        if not self.ssid or not self.password:
            print("[SERVER ERROR] Missing SSID or Password in config.txt!")
            return False
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print(f"[SERVER] Connecting to SSID: '{self.ssid}'...")
            self.wlan.connect(self.ssid, self.password)
            attempt = 0
            while not self.wlan.isconnected() and attempt < self.max_attempts:
                time.sleep(1)
                attempt += 1
                print(".", end="")
            print()
        if self.wlan.isconnected():
            ip_info = self.wlan.ifconfig()
            print("[SERVER] Wi-Fi Connected successfully!")
            print(f"[SERVER] IP Address: {ip_info[0]} | Subnet: {ip_info[1]} | Gateway: {ip_info[2]}")
            return True
        else:
            print(f"[SERVER] Failed to connect to SSID: '{self.ssid}'.")
            return False

    def is_connected(self):
        return self.wlan.isconnected()

    def get_ip(self):
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None
import neopixel
import machine
import time
from Weather.weatherLighting import WeatherLighting
from Server import Server
from OTA.OTAService import GitHubOTAUpdater

DataPin   = 0  # The GPIO pin used on the board 
NumLED    = 30 # The number of LEDs in the light strip
NeoLights = neopixel.NeoPixel(machine.Pin(DataPin), NumLED)
Lighting  = WeatherLighting(30, "Victoria BC", 30)
PrevArray = []

def set_brightness(color, brightness):
  r, g, b = color
  r = int(r * brightness)
  g = int(g * brightness)
  b = int(b * brightness)
  return (r, g, b)

def loop():
  global PrevArray
  array = Lighting.GetLightPattern()
  
  if(array == PrevArray):
      return # Nothing to update

  PrevArray = array
  for i in range(NumLED):
      NeoLights[i] = array[i]
  NeoLights.write()


# PUBLIC GITHUB OTA CONFIGURATION
GITHUB_REPO = "jonesbones99/WeatherArt"
GITHUB_BRANCH = "main"
def mark_healthy_boot():
    """Resets the crash count after app runs stably for 10 seconds."""
    try:
        with open("crash_count.txt", "w") as f:
            f.write("0")
        print("[HEALTH CHECK] Boot crash counter reset to 0.")
    except Exception as e:
        print("[HEALTH CHECK] Failed to reset crash counter:", e)
def run_github_ota():
    print(f"[OTA] Initializing GitHub OTA for '{GITHUB_REPO}'...")
    updater = GitHubOTAUpdater(
        github_repo=GITHUB_REPO,
        branch=GITHUB_BRANCH,
        manifest_file="version.json"
    )
    
    manifest = updater.check_for_update()
    if manifest:
        try:
            updater.apply_update(manifest)
        except Exception as e:
            print("[OTA ERROR] Failed to apply update from GitHub:", e)

def main():
    print("==================================================")
    print(" Pico W IoT Application (v1.0.0)")
    print("==================================================")
    # Instantiate Server class to load config.txt and connect to Wi-Fi
    server = Server(config_file="config.txt")
    if server.connect():
        run_github_ota()
    # Wait 10 seconds of stable runtime before clearing crash counter
    time.sleep(10)
    mark_healthy_boot()
  
    # Main Application Work Loop
    print("[APP] Main loop active...")
    counter = 0
    while True:
      loop()
      time.sleep(0.1)

if __name__ == "__main__":
    main()

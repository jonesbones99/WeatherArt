from DataModels.weatherEnum import Weather
from API.weatherAPI import WeatherAPI
from machine import Timer
import random
import time

CloudUpdateRate = 500 # Update rate in MS
CurrentWeather    = Weather.LIGHTNING # The current weather
WeatherService    = None # The serviced used to get the current weather
  
def GetTimeMS():
  return time.time() * 1000

class WeatherLighting:
  SunRise           = None # The time the sunrises
  SunSet            = None # The time the sunsets
  LastUpdate        = None
  NumLED            = 0
  def __init__(self, weatherPeriod, location, numLED):
    global WeatherService, CurrentWeather
    WeatherService       = WeatherAPI(30, "Victoria, BC")
    self.Period          = weatherPeriod
    self.Location        = location
    self.NumLED          = numLED
    self.LightingPattern = []
    self.LastUpdate		 = 0
    WeatherTimer         = Timer()
    WeatherTimer.init(mode=Timer.PERIODIC, callback=WeatherLighting.UpdateWeather, period=10000)
  
  def UpdateWeather(self):
    global WeatherService, CurrentWeather
    CurrentWeather = Weather.HOT
    print("[WeatherLighting] Upadting Weather from API")
    return

  def GetLightPattern(self):
    self.SetLightingPattern()
    print("[WeatherLighting] Get Lighting Pattern")
    return self.LightingPattern
  
  def SetLightingPattern(self):
    global CurrentWeather
    if CurrentWeather == Weather.UNKNOWN:
      self.DisplayUnknow()
      return
    elif CurrentWeather == Weather.SUN:
      self.DisplaySun()
      return
    elif CurrentWeather == Weather.CLOUD:
      self.DisplayCloud()
      return
    elif CurrentWeather == Weather.RAIN:
      self.DisplayRain()
      return
    elif CurrentWeather == Weather.SNOW:
      self.DisplaySnow()
      return
    elif CurrentWeather == Weather.LIGHTNING:
      self.DisplayLightning()
      return
    elif CurrentWeather == Weather.HOT:
      self.DisplayHot()
      return
    elif CurrentWeather == Weather.COLD:
      self.DisplayCold()
      return
    elif CurrentWeather == Weather.XMAS:
      self.DisplayXmas()
      return
    elif CurrentWeather == Weather.NEWYEARS:
      self.DisplayNewYears()
      return
    else:
      self.DisplayUnknow()
      return
    
  # Different Types of Weather 
  def DisplayUnknow(self):
    pattern = []
    for i in range(self.NumLED):
      pattern.append((80,80,80))
    self.LightingPattern = pattern

  def DisplaySun(self):
    pattern = []
    for i in range(self.NumLED):
      pattern.append((255,160,0))
    self.LightingPattern = pattern

  def DisplayCloud(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      if(random.randint(0, 1) == 0):
        pattern.append((255,255,255))
      else:
        pattern.append((128,128,128))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return

  def DisplayRain(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      if(random.randint(0, 1) == 0):
        pattern.append((200,200,200))
      else:
        pattern.append((23,51,168))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return

  def DisplaySnow(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      intensity = random.randint(0, 255)
      pattern.append((intensity,intensity,intensity))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return

  def DisplayLightning(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      if(random.randint(0, 1) == 0):
        pattern.append((40,40,40))
      else:
        pattern.append((34,29,190))
      if(random.randint(0, 80) == 0):
        pattern.append((255,255,0))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return

  def DisplayHot(self):
    pattern = []
    for i in range(self.NumLED):
      pattern.append((255,69,0))
    self.LightingPattern = pattern

  def DisplayCold(self):
    pattern = []
    for i in range(self.NumLED):
      pattern.append((29,46,104))
    self.LightingPattern = pattern

  def DisplayXmas(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      if(random.randint(0, 1) == 0):
        pattern.append((255,0,0))
      else:
        pattern.append((0,255,0))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return

  def DisplayNewYears(self):
    pattern = []
    if((GetTimeMS() - self.LastUpdate) < CloudUpdateRate):
      return
    for i in range(self.NumLED):
      pattern.append((random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)))
    self.LightingPattern = pattern
    self.LastUpdate = GetTimeMS()
    return



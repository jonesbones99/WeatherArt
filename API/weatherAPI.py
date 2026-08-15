class WeatherAPI:
  Period   = 30 # How often to check the weather in minutes
  Location = "" # The location to check the weather for
  def __init__(self, period, location):
    self.Period = period
    self.Location = location

  def GetWeather(self):
    print("Hello my name is")
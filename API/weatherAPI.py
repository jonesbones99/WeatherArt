import urequests
from urllib.parse import quote
from DataModels.weatherEnum import Weather

class WeatherAPI:
  Period   = 30 # How often to check the weather in minutes
  Location = "" # The location to check the weather for
  def __init__(self, period, location):
    self.Period = period
    self.Location = location

  def GetWeather(self):
    """
    Fetches the current weather at the given location (city name or latitude,longitude)
    and returns the weather as a Weather enum value.
    """
    try:
      latitude, longitude = self._resolve_lat_lon()

      # Fetch current weather data
      weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={quote(str(latitude))}&longitude={quote(str(longitude))}&current=weather_code,temperature_2m&timezone=auto"
      weather_response = urequests.get(weather_url)
      weather_data = weather_response.json()
      weather_response.close()
      
      weather_code = weather_data["current"]["weather_code"]
      temperature = weather_data["current"]["temperature_2m"]
      
      # Convert WMO weather code to Weather enum
      return self._weather_code_to_enum(weather_code, temperature)
    
    except Exception as e:
      print(f"Error fetching weather: {e}")
      return Weather.UNKNOWN

  def _resolve_lat_lon(self):
    location = str(self.Location).strip()

    # Support a direct latitude/longitude pair such as "48.4359, -123.35155"
    if location:
      parts = [part.strip() for part in location.replace(";", ",").split(",")]
      if len(parts) >= 2:
        try:
          latitude = float(parts[0])
          longitude = float(parts[1])
          return latitude, longitude
        except ValueError:
          pass

    # Otherwise geocode the city name to get latitude and longitude.
    # The location must be URL-encoded so spaces and commas are valid in query strings.
    encoded_location = quote(location)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_location}&count=1&language=en&format=json"
    geo_response = urequests.get(geo_url)
    geo_data = geo_response.json()
    geo_response.close()
    
    if not geo_data.get("results"):
      raise ValueError("No weather location found")
    
    location_data = geo_data["results"][0]
    return location_data["latitude"], location_data["longitude"]
  
  def _weather_code_to_enum(self, code, temperature):
    """
    Convert WMO weather code and temperature to Weather enum.
    WMO codes: 0=Clear, 1-2=Partly Cloudy, 3=Overcast, 45=Foggy, 48=Foggy,
               51-67=Drizzle/Rain, 71-77=Snow, 80-82=Rain Showers, 85-86=Snow Showers,
               80-99=Thunderstorm
    """
    if code == 0:
      return Weather.SUN
    elif code in [1, 2]:
      return Weather.CLOUD
    elif code == 3:
      return Weather.CLOUD
    elif code in [45, 48]:
      return Weather.CLOUD
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
      return Weather.RAIN
    elif code in [71, 73, 75, 77, 85, 86]:
      return Weather.SNOW
    elif code in [80, 81, 82, 85, 86]:
      return Weather.RAIN if code < 85 else Weather.SNOW
    elif code in [95, 96, 99]:
      return Weather.LIGHTNING
    else:
      if temperature > 30:
        return Weather.HOT
      elif temperature < 0:
        return Weather.COLD
      return Weather.UNKNOWN
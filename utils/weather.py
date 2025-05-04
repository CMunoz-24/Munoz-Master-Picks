
import os
import requests
from dotenv import load_dotenv
from utils.weather_teams import TEAM_LOCATIONS

load_dotenv()

WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY", "115c9056840819162f244cdfee6bd371")

def get_weather_adjustments(matchup_name):
    for team in TEAM_LOCATIONS:
        if team in matchup_name:
            lat = TEAM_LOCATIONS[team]["lat"]
            lon = TEAM_LOCATIONS[team]["lon"]
            break
    else:
        return {"conditions": "Location unknown", "adjustments": {}}

    try:
        open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,windspeed_10m&current_weather=true"
        response = requests.get(open_meteo_url)
        data = response.json()
        current = data.get("current_weather", {})

        temp = current.get("temperature")
        wind = current.get("windspeed")

        # Add adjustment logic
        adjustments = {
            "HR Boost": "+10%" if temp and temp > 80 and wind and wind > 12 else "Neutral",
            "Strikeout Drop": "-5%" if wind and wind > 15 else "Neutral",
        }

        return {
            "conditions": f"{temp}°C, Wind {wind} km/h",
            "adjustments": adjustments
        }

    except Exception as e:
        print(f"[WEATHER ERROR] Failed to fetch weather: {e}")
        return {
            "conditions": "Weather unavailable",
            "adjustments": {}
        }

def get_weatherstack_weather(city):
    try:
        url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={city}"
        res = requests.get(url)
        data = res.json()
        if "current" in data:
            return {
                "source": "weatherstack",
                "temperature": data["current"].get("temperature"),
                "wind_speed": data["current"].get("wind_speed"),
                "humidity": data["current"].get("humidity"),
                "precip": data["current"].get("precip"),
                "description": data["current"].get("weather_descriptions", ["N/A"])[0],
            }
    except Exception as e:
        print(f"[ERROR] Weatherstack failed: {e}")
    return None

def get_open_meteo_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url)
        data = res.json()
        if "current_weather" in data:
            weather = data["current_weather"]
            return {
                "source": "open-meteo",
                "temperature": weather.get("temperature"),
                "wind_speed": weather.get("windspeed"),
                "wind_direction": weather.get("winddirection"),
                "precip": weather.get("precipitation", 0),
                "description": f"Wind {weather.get('windspeed')} km/h from {weather.get('winddirection')}°"
            }
    except Exception as e:
        print(f"[ERROR] Open-Meteo failed: {e}")
    return None

def get_combined_weather(city, lat=None, lon=None):
    weather = get_weatherstack_weather(city)
    if not weather and lat is not None and lon is not None:
        weather = get_open_meteo_weather(lat, lon)
    return weather or {"error": "Weather data unavailable"}

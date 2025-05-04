
import requests
from utils.weather_teams import get_coordinates_for_team
import os

# For Weatherstack API
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")

def get_weather_adjustments(team_name):
    coords = get_coordinates_for_team(team_name)
    if not coords:
        return {
            "adjustments": {},
            "conditions": "Location unknown"
        }

    lat, lon = coords
    try:
        # Call Open-Meteo
        open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(open_meteo_url)
        data = res.json()
        current = data.get("current_weather", {})

        temp = current.get("temperature", 70)
        windspeed = current.get("windspeed", 0)
        wind_dir = current.get("winddirection", 0)

        conditions = f"{temp}°F, {windspeed}mph wind"

        adjustments = {}

        if temp >= 80 and windspeed >= 10:
            adjustments["HR Boost"] = "+10%"

        if windspeed >= 12:
            adjustments["Strikeout Drop"] = "-5%"

        return {
            "adjustments": adjustments,
            "conditions": conditions
        }

    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        return {
            "adjustments": {},
            "conditions": "Unavailable"
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

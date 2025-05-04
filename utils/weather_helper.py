
import requests
import os
from datetime import datetime, timedelta

WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")

def fetch_weatherstack_weather(lat, lon):
    try:
        url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_KEY}&query={lat},{lon}&units=f"
        res = requests.get(url)
        data = res.json()
        if "current" in data:
            return {
                "source": "Weatherstack",
                "temperature": data["current"]["temperature"],
                "wind_speed": data["current"]["wind_speed"],
                "wind_dir": data["current"]["wind_dir"],
                "precip": data["current"]["precip"],
                "cloudcover": data["current"]["cloudcover"],
                "description": data["current"]["weather_descriptions"][0] if data["current"]["weather_descriptions"] else "Unknown"
            }
    except Exception as e:
        print(f"[Weatherstack ERROR] {e}")
    return {}

def fetch_openmeteo_weather(lat, lon):
    try:
        now = datetime.utcnow()
        hour = now.replace(minute=0, second=0, microsecond=0).isoformat() + "Z"
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,cloudcover,windspeed_10m&start={hour}&end={hour}"
        res = requests.get(url)
        data = res.json()
        if "hourly" in data:
            return {
                "source": "Open-Meteo",
                "temperature": data["hourly"]["temperature_2m"][0],
                "wind_speed": data["hourly"]["windspeed_10m"][0],
                "cloudcover": data["hourly"]["cloudcover"][0],
                "precip": data["hourly"]["precipitation"][0],
            }
    except Exception as e:
        print(f"[Open-Meteo ERROR] {e}")
    return {}

def get_combined_weather(lat, lon):
    ws = fetch_weatherstack_weather(lat, lon)
    om = fetch_openmeteo_weather(lat, lon)

    return {
        "temperature": ws.get("temperature", om.get("temperature")),
        "wind_speed": ws.get("wind_speed", om.get("wind_speed")),
        "wind_dir": ws.get("wind_dir", "N/A"),
        "precip": ws.get("precip", om.get("precip")),
        "cloudcover": ws.get("cloudcover", om.get("cloudcover")),
        "description": ws.get("description", "N/A"),
        "source": ws.get("source", om.get("source", "Unknown")),
    }

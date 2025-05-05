
import requests
import os

# For Weatherstack API
WEATHERSTACK_API_KEY = os.getenv("WEATHERSTACK_API_KEY")

# Stadium coordinates for weather-based adjustments
park_coordinates = {
    "Yankee Stadium": (40.8296, -73.9262),
    "Fenway Park": (42.3467, -71.0972),
    "Rogers Centre": (43.6414, -79.3894),
    "Tropicana Field": (27.7683, -82.6534),  # not used this year
    "George M. Steinbrenner Field": (27.9759, -82.5033),  # Rays temp home
    "Oriole Park at Camden Yards": (39.2839, -76.6219),
    "Progressive Field": (41.4962, -81.6852),
    "Comerica Park": (42.3390, -83.0485),
    "Guaranteed Rate Field": (41.8299, -87.6338),
    "Kauffman Stadium": (39.0517, -94.4803),
    "Target Field": (44.9817, -93.2789),
    "Minute Maid Park": (29.7573, -95.3555),
    "Angel Stadium": (33.8003, -117.8827),
    "RingCentral Coliseum": (37.7516, -122.2005),  # not used this year
    "Sutter Health Park": (38.5802, -121.5131),  # Athletics temp home
    "T-Mobile Park": (47.5914, -122.3325),
    "Globe Life Field": (32.7473, -97.0847),
    "Citizens Bank Park": (39.9061, -75.1665),
    "Truist Park": (33.8908, -84.4678),
    "loanDepot Park": (25.7780, -80.2195),
    "Nationals Park": (38.8730, -77.0074),
    "Wrigley Field": (41.9484, -87.6553),
    "Great American Ball Park": (39.0975, -84.5070),
    "American Family Field": (43.0280, -87.9711),
    "PNC Park": (40.4469, -80.0057),
    "Busch Stadium": (38.6226, -90.1928),
    "Chase Field": (33.4455, -112.0667),
    "Coors Field": (39.7559, -104.9942),
    "Dodger Stadium": (34.0739, -118.2400),
    "Petco Park": (32.7073, -117.1573),
    "Oracle Park": (37.7786, -122.3893),
}

def get_coordinates_for_team(park_name):
    return park_coordinates.get(park_name, (None, None))

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

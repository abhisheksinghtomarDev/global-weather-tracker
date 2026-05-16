#!/usr/bin/env python3
"""
Weather Data Fetcher Agent
Uses Open-Meteo API (FREE, no API key required)
Fetches current weather and 24-hour historical data for all cities
"""
import requests
import json
import os
import time
from datetime import datetime, timedelta

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_DELAY = 0  # no delay - Open-Meteo handles high throughput

class WeatherFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.historical_url = "https://archive-api.open-meteo.com/v1/archive"
        self.cities = self._load_cities()

    def _load_cities(self):
        """Load city database"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), "data")
        cities_file = os.path.join(data_dir, "cities.json")

        with open(cities_file, 'r') as f:
            return json.load(f)

    def fetch_with_retry(self, url, params, timeout=10):
        """Fetch with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    print(f"    Rate limited, waiting {RETRY_DELAY * (attempt + 1)}s...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"    Retry {attempt + 1}/{MAX_RETRIES} after error: {e}")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"    Failed after {MAX_RETRIES} attempts: {e}")
                    return None
        return None

    def fetch_current_weather(self, lat, lon):
        """Fetch current weather for a location"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "auto"
        }

        data = self.fetch_with_retry(self.base_url, params, timeout=10)
        return data.get("current", {}) if data else None

    def fetch_historical_weather(self, lat, lon, hours=24):
        """Fetch historical weather data for last N hours"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d"),
            "hourly": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto"
        }

        data = self.fetch_with_retry(self.historical_url, params, timeout=30)
        return data.get("hourly", {}) if data else None

    def fetch_all_cities_weather(self):
        """Fetch weather for all cities in database"""
        results = []
        total_countries = len(self.cities["countries"])

        print(f"  🌍 Fetching weather for {total_countries} countries...")

        for country_data in self.cities["countries"]:
            country_name = country_data["name"]
            country_code = country_data["code"]
            cities = country_data["cities"]

            print(f"    📍 Processing {country_name} ({len(cities)} cities)...")

            for city in cities:
                city_name = city["name"]
                lat = city["lat"]
                lon = city["lon"]

                # Rate limiting delay between cities
                time.sleep(REQUEST_DELAY)

                # Fetch current weather
                current = self.fetch_current_weather(lat, lon)

                # Fetch historical data (last 24 hours)
                historical = self.fetch_historical_weather(lat, lon, hours=24)

                city_data = {
                    "country": country_name,
                    "country_code": country_code,
                    "city": city_name,
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": datetime.utcnow().isoformat(),
                    "current": current,
                    "history_24h": historical
                }

                results.append(city_data)
                print(f"      ✅ {city_name}")

        return results

    def get_weather_summary(self, all_data):
        """Generate summary statistics from all weather data"""
        if not all_data:
            return {}

        temperatures = []
        humidities = []

        for city_data in all_data:
            current = city_data.get("current", {})
            if current and "temperature_2m" in current:
                temp = current.get("temperature_2m")
                if temp is not None:
                    temperatures.append(temp)

            if current and "relative_humidity_2m" in current:
                humid = current.get("relative_humidity_2m")
                if humid is not None:
                    humidities.append(humid)

        return {
            "total_cities": len(all_data),
            "avg_temperature": round(sum(temperatures) / len(temperatures), 2) if temperatures else 0,
            "avg_humidity": round(sum(humidities) / len(humidities), 2) if humidities else 0,
            "hottest_city": max(all_data, key=lambda x: x.get("current", {}).get("temperature_2m", 0))["city"] if temperatures else "N/A",
            "coldest_city": min(all_data, key=lambda x: x.get("current", {}).get("temperature_2m", 100))["city"] if temperatures else "N/A"
        }

if __name__ == "__main__":
    fetcher = WeatherFetcher()
    print("  🌤️ Starting weather fetch...")
    data = fetcher.fetch_all_cities_weather()
    print(f"\n  ✅ Fetched weather for {len(data)} cities!")
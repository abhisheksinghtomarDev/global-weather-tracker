#!/usr/bin/env python3
"""
Weather Data Fetcher Agent
Uses Open-Meteo API (FREE, no API key required)
Fetches current weather for all cities with parallel requests
"""
import requests
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_RETRIES = 3
RETRY_DELAY = 1
MAX_WORKERS = 20  # parallel requests

class WeatherFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.cities = self._load_cities()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "GlobalWeatherTracker/1.0"})

    def _load_cities(self):
        """Load city database"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), "data")
        cities_file = os.path.join(data_dir, "cities.json")

        with open(cities_file, 'r') as f:
            return json.load(f)

    def fetch_with_retry(self, url, params, timeout=15):
        """Fetch with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
        return None

    def fetch_city_weather(self, city_info):
        """Fetch weather for a single city"""
        city_name = city_info["name"]
        lat = city_info["lat"]
        lon = city_info["lon"]
        country = city_info["country"]
        country_code = city_info["country_code"]

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "auto"
        }

        data = self.fetch_with_retry(self.base_url, params)
        current = data.get("current", {}) if data else None

        return {
            "country": country,
            "country_code": country_code,
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().isoformat(),
            "current": current,
            "history_24h": None
        }

    def fetch_all_cities_weather(self):
        """Fetch weather for all cities in database using parallel requests"""
        # Build list of all cities with their metadata
        all_cities = []
        for country_data in self.cities["countries"]:
            for city in country_data["cities"]:
                all_cities.append({
                    "name": city["name"],
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "country": country_data["name"],
                    "country_code": country_data["code"]
                })

        total = len(all_cities)
        print(f"  🌍 Fetching weather for {total} cities (parallel)...")

        results = []
        completed = 0
        failed = 0

        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.fetch_city_weather, city): city for city in all_cities}

            for future in as_completed(futures):
                city = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    if completed % 20 == 0:
                        print(f"    📊 Progress: {completed}/{total} cities")
                except Exception as e:
                    failed += 1
                    print(f"    ❌ Failed: {city['name']} - {e}")

        print(f"  ✅ Completed: {completed}, Failed: {failed}")
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

        if not temperatures:
            return {"total_cities": 0}

        return {
            "total_cities": len(all_data),
            "avg_temperature": round(sum(temperatures) / len(temperatures), 2),
            "avg_humidity": round(sum(humidities) / len(humidities), 2),
            "hottest_city": max(all_data, key=lambda x: x.get("current", {}).get("temperature_2m", 0))["city"],
            "coldest_city": min(all_data, key=lambda x: x.get("current", {}).get("temperature_2m", 100))["city"]
        }

if __name__ == "__main__":
    fetcher = WeatherFetcher()
    print("  🌤️ Starting weather fetch...")
    data = fetcher.fetch_all_cities_weather()
    print(f"\n  ✅ Fetched weather for {len(data)} cities!")
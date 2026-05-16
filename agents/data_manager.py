#!/usr/bin/env python3
"""
Data Manager Agent
Manages saving weather data to JSON and CSV files
Organizes data by country and date
"""
import json
import os
import csv
from datetime import datetime

class DataManager:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(script_dir)
        self.data_dir = os.path.join(self.base_dir, "data")
        self.countries_dir = os.path.join(self.data_dir, "countries")

        # Ensure directories exist
        os.makedirs(self.countries_dir, exist_ok=True)

    def save_weather_data(self, weather_data, summary):
        """Save all weather data to files"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. Save main data file with all cities
        main_file = os.path.join(self.data_dir, f"weather_data_{today}.json")
        with open(main_file, 'w') as f:
            json.dump({
                "date": today,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": summary,
                "cities": weather_data
            }, f, indent=2)
        print(f"  💾 Saved main data: weather_data_{today}.json")

        # 2. Save individual country files
        self._save_country_files(weather_data, today)

        # 3. Save CSV for each city (append mode for history)
        self._save_city_csv_files(weather_data, today)

        # 4. Update master data file (latest)
        self._update_master_file(weather_data, summary)

        return main_file

    def _save_country_files(self, weather_data, date):
        """Save weather data organized by country"""
        # Group by country
        countries_data = {}
        for city_data in weather_data:
            country = city_data["country"]
            if country not in countries_data:
                countries_data[country] = []
            countries_data[country].append(city_data)

        # Save each country
        for country, cities in countries_data.items():
            country_file = country.lower().replace(" ", "_") + ".json"
            country_path = os.path.join(self.countries_dir, country_file)

            with open(country_path, 'w') as f:
                json.dump({
                    "country": country,
                    "date": date,
                    "cities": cities
                }, f, indent=2)

    def _save_city_csv_files(self, weather_data, date):
        """Save individual city CSV files (append to history)"""
        csv_dir = os.path.join(self.data_dir, "cities_csv")
        os.makedirs(csv_dir, exist_ok=True)

        for city_data in weather_data:
            country = city_data["country"]
            city = city_data["city"]
            current = city_data.get("current", {})

            # Create safe filename
            safe_country = "".join(c for c in country if c.isalnum())
            safe_city = "".join(c for c in city if c.isalnum())
            csv_filename = f"{safe_country}_{safe_city}.csv"
            csv_path = os.path.join(csv_dir, csv_filename)

            # CSV headers
            fieldnames = ["date", "country", "city", "temperature", "humidity", "feels_like", "weather_code", "wind_speed", "wind_direction"]

            # Check if file exists (to append or create)
            file_exists = os.path.exists(csv_path)

            with open(csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                row = {
                    "date": date,
                    "country": country,
                    "city": city,
                    "temperature": current.get("temperature_2m", ""),
                    "humidity": current.get("relative_humidity_2m", ""),
                    "feels_like": current.get("apparent_temperature", ""),
                    "weather_code": current.get("weather_code", ""),
                    "wind_speed": current.get("wind_speed_10m", ""),
                    "wind_direction": current.get("wind_direction_10m", "")
                }
                writer.writerow(row)

    def _update_master_file(self, weather_data, summary):
        """Update master weather data file with latest data"""
        master_file = os.path.join(self.data_dir, "latest_weather.json")

        with open(master_file, 'w') as f:
            json.dump({
                "last_updated": datetime.utcnow().isoformat(),
                "summary": summary,
                "cities": weather_data
            }, f, indent=2)

        print(f"  💾 Updated master file: latest_weather.json")

    def get_data_file_path(self):
        """Get path to today's data file for GitHub commit"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.data_dir, f"weather_data_{today}.json")

if __name__ == "__main__":
    dm = DataManager()
    print("  📁 Data Manager initialized")
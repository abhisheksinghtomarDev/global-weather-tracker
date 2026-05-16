#!/usr/bin/env python3
"""
Main Weather Contributor Agent
Orchestrates: Fetch weather → Save data → Generate README → Ready for commit
"""
import os
import sys
from datetime import datetime

# Add agents to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_fetcher import WeatherFetcher
from data_manager import DataManager
from readme_generator import ReadmeGenerator

def main():
    print("=" * 60)
    print(f"🌍 Global Weather Tracker - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)

    # Step 1: Fetch weather data
    print("\n📥 Step 1: Fetching weather data from Open-Meteo...")
    fetcher = WeatherFetcher()
    weather_data = fetcher.fetch_all_cities_weather()

    if not weather_data:
        print("  ❌ Failed to fetch weather data!")
        return

    print(f"  ✅ Fetched data for {len(weather_data)} cities")

    # Step 2: Generate summary
    print("\n📊 Step 2: Generating summary statistics...")
    summary = fetcher.get_weather_summary(weather_data)
    print(f"  🌡️  Avg Temp: {summary.get('avg_temperature', 0)}°C")
    print(f"  💧 Avg Humidity: {summary.get('avg_humidity', 0)}%")
    print(f"  🔥 Hottest: {summary.get('hottest_city', 'N/A')}")
    print(f"  ❄️  Coldest: {summary.get('coldest_city', 'N/A')}")

    # Step 3: Save data to files
    print("\n💾 Step 3: Saving data to files...")
    dm = DataManager()
    main_file = dm.save_weather_data(weather_data, summary)

    # Step 4: Generate README
    print("\n📝 Step 4: Generating README...")
    gen = ReadmeGenerator()
    readme_content = gen.generate_readme(weather_data, summary)
    readme_path = gen.save_readme(readme_content)

    # Summary
    print("\n" + "=" * 60)
    print("✅ DAILY WEATHER DATA COLLECTION COMPLETE!")
    print("=" * 60)
    print(f"  📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  🌍 Cities tracked: {len(weather_data)}")
    print(f"  📁 Data files: Updated")
    print(f"  📖 README: Updated")
    print("  🎉 Ready for GitHub commit!")
    print("=" * 60)

    return readme_path

if __name__ == "__main__":
    main()
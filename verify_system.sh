#!/bin/bash

echo "🔍 Checking Muñoz Master Picks system..."

# Check for get_park_adjustments import
echo "🔎 Scanning for missing 'get_park_adjustments' import in main.py..."
grep -q "get_park_adjustments" main.py && \
grep -q "from park_factors import get_park_adjustments" main.py || \
echo "❌ Missing 'get_park_adjustments' import in main.py"

# Check if fallback_stats.csv exists in /data
echo "📁 Checking for fallback_stats.csv..."
if [ ! -f "data/fallback_stats.csv" ]; then
  echo "❌ fallback_stats.csv missing from /data"
  if [ -f "fallback_stats.csv" ]; then
    echo "✅ Found in root. Moving to /data..."
    mkdir -p data && mv fallback_stats.csv data/
  fi
else
  echo "✅ fallback_stats.csv found"
fi

# Check if batter_vs_pitcher.csv exists in /data
echo "📁 Checking for batter_vs_pitcher.csv..."
if [ ! -f "data/batter_vs_pitcher.csv" ]; then
  echo "❌ batter_vs_pitcher.csv missing from /data"
  if [ -f "batter_vs_pitcher.csv" ]; then
    echo "✅ Found in root. Moving to /data..."
    mkdir -p data && mv batter_vs_pitcher.csv data/
  fi
else
  echo "✅ batter_vs_pitcher.csv found"
fi

# Check if .env is sourced and contains key
echo "🔐 Checking for .env file and ODDS_API_KEY..."
if [ ! -f ".env" ]; then
  echo "❌ .env file not found!"
elif ! grep -q "ODDS_API_KEY=" .env; then
  echo "❌ ODDS_API_KEY not set in .env!"
else
  echo "✅ .env file exists with API key"
  export $(grep -v '^#' .env | xargs) # source it
fi

# Done
echo "✅ Check complete. You're ready to restart."

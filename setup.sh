#!/bin/bash

echo "🚀 Setting up YouTube Migrater..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data folder
mkdir -p data

# Ask user for client_secret.json
if [ ! -f "data/client_secret.json" ]; then
  echo "⚠️ Please download your Google API client_secret.json file"
  echo "   from https://console.cloud.google.com/apis/credentials"
  echo "   and place it at: $(pwd)/data/client_secret.json"
fi

# First run to trigger login
echo "🔑 Authenticating with Google..."
python - <<EOF
from youtube_migrater import migration
migration.CREDENTIALS_FILE = "data/client_secret.json"
migration.TOKEN_FILE = "data/token.json"
migration.get_authenticated_service()
print("✅ Authentication successful! Token saved in data/token.json")
EOF

echo "📂 Please place your MyActivity.html file in: $(pwd)/data"
echo "✨ Setup complete! Run with: youtube-migrater --takeout data/MyActivity.html --credentials data/client_secret.json"
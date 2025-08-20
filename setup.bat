@echo off
echo 🚀 Setting up YouTube Migrater...

REM Create virtual environment
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create data folder
if not exist data (
    mkdir data
)

REM Ask user for client_secret.json
if not exist data\client_secret.json (
    echo ⚠️ Please download your Google API client_secret.json file
    echo from https://console.cloud.google.com/apis/credentials
    echo and place it at: %cd%\data\client_secret.json
)

REM First run to trigger login
echo 🔑 Authenticating with Google...
python - <<EOF
from youtube_migrater import migration
migration.CREDENTIALS_FILE = "data/client_secret.json"
migration.TOKEN_FILE = "data/token.json"
migration.get_authenticated_service()
print("✅ Authentication successful! Token saved in data/token.json")
EOF

echo 📂 Please place your MyActivity.html file in: %cd%\data
echo ✨ Setup complete! Run with: youtube-migrater --takeout data\MyActivity.html --credentials data\client_secret.json

# 🎬 YouTube Migrator

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**Seamlessly migrate your YouTube data - subscriptions, likes, and watch history - from Google Takeout to a new account.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [FAQ](#-faq)

</div>

---

## ✨ Features

- 🔄 **Multi-Format Support**: Parse HTML and CSV files from Google Takeout
- 📊 **Intelligent Parsing**: Automatically detects and parses subscriptions, liked videos, and watch history
- 🛡️ **Duplicate Prevention**: Smart merge system ensures no duplicate entries
- 📈 **Progress Tracking**: Resume migrations from where you left off
- 🎯 **Quota Management**: Built-in YouTube API quota monitoring and management
- ⚡ **Batch Processing**: Control how many items to process per run
- 🔐 **Secure Authentication**: OAuth 2.0 authentication with Google
- 🎨 **User-Friendly**: Interactive prompts and colorful console output

---

## 📋 Prerequisites

- Python 3.8 or higher
- A Google Cloud Project with YouTube Data API v3 enabled
- Google Takeout data (HTML or CSV format)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/cysec-wht24/youtube-migrator.git
cd youtube-migrator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials JSON file
6. Rename it to `client_secret.json` and place it in the `data/` folder

### 4. Export Your YouTube Data

1. Visit [Google Takeout](https://takeout.google.com/)
2. Deselect all, then select only **YouTube and YouTube Music**
3. Click "All YouTube data included" and select:
   - ✅ subscriptions
   - ✅ liked videos
   - ✅ watch history
4. Choose delivery method and export
5. Extract the files and place them in the `data/` folder

---

## 📖 Usage

### Basic Usage

```bash
python migration.py
```

### Workflow

1. **Authentication**: The script will open a browser for Google OAuth login (first run only)
2. **File Detection**: Automatically detects available HTML and CSV files in `data/` folder
3. **File Selection**: Choose which file to parse (e.g., `subscriptions.csv`, `MyActivity.html`)
4. **Migration Options**: Select what to migrate (likes, subscriptions, or both)
5. **Processing**: The script processes your data with progress indicators

### Supported File Formats

| File Type | Description | Parsed Data |
|-----------|-------------|-------------|
| `MyActivity.html` | Complete YouTube activity | Subscriptions, Likes, Watch History |
| `subscriptions.csv` | Channel subscriptions | Subscriptions |
| `music library songs.csv` | Music library | Liked Videos |

---

## ⚙️ Configuration

Edit the constants at the top of `migration.py`:

```python
API_DELAY = 5  # Seconds between API calls
MAX_SUBSCRIPTIONS_PER_RUN = 50  # Max subscriptions per run
MAX_LIKES_PER_RUN = 100  # Max likes per run
QUOTA_LIMIT = 10000  # Daily YouTube API quota limit
```

---

## 📂 Project Structure

```
youtube-migrator/
│
├── migration.py              # Main script
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
└── data/                     # Data directory (create this)
    ├── client_secret.json    # Google API credentials (you provide)
    ├── token.json            # OAuth token (auto-generated)
    ├── MyActivity.html       # YouTube Takeout HTML (optional)
    ├── subscriptions.csv     # Subscriptions CSV (optional)
    ├── music library songs.csv  # Music library CSV (optional)
    ├── parsed_activity.json  # Parsed data (auto-generated)
    ├── progress.json         # Migration progress (auto-generated)
    └── api_derived.json      # API data cache (auto-generated)
```

---

## 🔧 How It Works

### 1. **File Detection & Parsing**
The script scans the `data/` folder for HTML and CSV files, then parses them based on format:
- HTML: Extracts links and activity types
- CSV: Reads structured data (Channel IDs, Video IDs)

### 2. **Duplicate Prevention**
Uses set operations to merge new data with existing data, ensuring each URL appears only once.

### 3. **API Operations**
- **Subscriptions**: Uses `subscriptions.insert` (50 quota per request)
- **Likes**: Uses `videos.rate` (50 quota per request)
- Includes retry logic and quota monitoring

### 4. **Progress Tracking**
Saves progress after each successful operation, allowing you to resume if interrupted.

---

## 💡 Tips & Best Practices

- **Start Small**: Test with a small batch first (e.g., 10 subscriptions)
- **Monitor Quota**: The default quota is 10,000 units/day, which resets at midnight Pacific Time
- **Run Daily**: Process data in batches to stay within quota limits
- **Keep Backups**: Don't delete your Takeout files until migration is complete
- **CSV Advantages**: CSV files are faster to parse than large HTML files

---

## ❓ FAQ

### Q: What's the YouTube API quota limit?
**A:** Default is 10,000 units/day. Each subscription costs 50 units, each like costs 50 units.

### Q: Can I run this multiple times?
**A:** Yes! Progress is saved automatically. You can resume anytime.

### Q: Will this create duplicates?
**A:** No. The script uses set operations to prevent duplicates.

### Q: What if I hit the quota limit?
**A:** The script detects quota errors and shows when the quota resets (midnight Pacific Time).

### Q: Can I parse multiple files?
**A:** Yes. Run the script multiple times and select different files. Data merges automatically.

### Q: Does this work with Brand Accounts?
**A:** Yes, as long as you authenticate with the correct Google account.

---

## 🐛 Troubleshooting

### "Quota exceeded" error
Wait until midnight Pacific Time for quota reset, or request a quota increase from Google.

### "Channel not found" error
The channel may have been deleted or made private. The script will skip it automatically.

### Authentication issues
Delete `data/token.json` and re-run the script to re-authenticate.

### Parse errors
Ensure your Takeout files are properly extracted and in the `data/` folder.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Manomay Bisht**

- GitHub: [@cysec-wht24](https://github.com/cysec-wht24)

---

## ⚠️ Disclaimer

This tool is for personal use only. Use responsibly and in accordance with YouTube's Terms of Service. The authors are not responsible for any misuse or quota violations.

---

## 🌟 Star History

If this project helped you, please consider giving it a ⭐!

---

<div align="center">

**Made with ❤️ for the YouTube community**

[Report Bug](https://github.com/cysec-wht24/youtube-migrator/issues) · [Request Feature](https://github.com/cysec-wht24/youtube-migrator/issues)

</div>
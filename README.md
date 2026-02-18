# 🎬 YouTube Migrator

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)

**Migrate your YouTube subscriptions, likes, and watch history from Google Takeout to a new account.**

</div>

---

## ✨ Features

- 🔄 Multi-format support: HTML and CSV from Google Takeout
- 🛡️ Duplicate prevention via set operations
- 📈 Progress tracking — resume anytime
- 🎯 Built-in API quota monitoring
- 🐳 Docker support — no Python needed

---

## 📋 Before You Start

Regardless of cloned or Docker mode, you need:

1. **Google API credentials** — [Google Cloud Console](https://console.cloud.google.com/) → Enable YouTube Data API v3 → Create OAuth 2.0 Client ID (Desktop app) → Download JSON → rename to `client_secret.json`
2. **Takeout data** — [takeout.google.com](https://takeout.google.com) → Export YouTube data (subscriptions, liked videos, watch history) → extract files

---

## 🚀 Quick Start

### Option A — Cloned (Python)

```bash
git clone https://github.com/cysec-wht24/youtube-migrator.git
cd youtube-migrator
pip install -r requirements.txt
```

Place `client_secret.json` and Takeout files in `data/`, then:

```bash
python migration.py
```

A browser opens automatically for Google OAuth on first run.

---

### Option B — Docker (No Python Required)

```bash
docker pull ghcr.io/cysec-wht24/youtube-migrator:main
mkdir data
# place client_secret.json and Takeout files in data/
docker run -it --rm -v $(pwd)/data:/app/data ghcr.io/cysec-wht24/youtube-migrator:main
```

**First run:** A URL is printed — open it in your browser, log into the account you're migrating **to**, paste the code back. `token.json` is saved to `data/` and OAuth is skipped on all future runs.

> Or build locally: `./setup-docker.sh` — checks Docker, prompts for `client_secret.json` if missing, and builds the image.

---

## 📂 Data Folder

```
data/
├── client_secret.json        ← you provide (never committed to git)
├── token.json                ← auto-generated after first OAuth
├── MyActivity.html           ← Takeout file (optional)
├── subscriptions.csv         ← Takeout file (optional)
├── music library songs.csv   ← Takeout file (optional)
├── progress.json             ← auto-generated (resume state)
└── parsed_activity.json      ← auto-generated (cache)
```

---

## 📖 Usage

On each run the script will ask:

1. Which Takeout file to parse
2. What to migrate: likes, subscriptions, or both
3. How many items to process this run

Quota and progress are saved automatically after each operation.

### Supported File Formats

| File | Data |
|------|------|
| `MyActivity.html` | Subscriptions, Likes, Watch History |
| `subscriptions.csv` | Subscriptions |
| `music library songs.csv` | Liked Videos |

---

## ⚙️ Configuration

Edit constants at the top of `migration.py`:

```python
API_DELAY = 5                  # Seconds between API calls
MAX_SUBSCRIPTIONS_PER_RUN = 50
MAX_LIKES_PER_RUN = 100
QUOTA_LIMIT = 10000            # Daily YouTube API quota
```

---

## ❓ FAQ

**Q: Will this create duplicates?**
No — set operations prevent duplicates across runs.

**Q: What's the quota limit?**
10,000 units/day. Each subscription or like costs 50 units (~200 subs/day).

**Q: Quota exceeded?**
Script tells you exactly when it resets (midnight Pacific Time). Re-run then — progress is saved.

**Q: Is `client_secret.json` safe in Docker?**
Yes. It's mounted at runtime via a volume — never baked into the image, never committed to git.

**Q: Why does Docker print a URL instead of opening a browser?**
Containers have no display. It's a one-time step — after that `token.json` handles auth automatically.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| Auth issues | Delete `data/token.json` and re-run |
| Quota exceeded | Wait for midnight Pacific Time reset |
| Channel not found | Deleted/private channel — auto-skipped |
| Parse errors | Ensure Takeout files are extracted into `data/` |

---

## 📜 License & Disclaimer

GPL-3.0 — personal use only. Use responsibly and in accordance with YouTube's Terms of Service.

---

<div align="center">

**Made with ❤️ for the YouTube community**

[Report Bug](https://github.com/cysec-wht24/youtube-migrator/issues) · [Request Feature](https://github.com/cysec-wht24/youtube-migrator/issues)

</div>

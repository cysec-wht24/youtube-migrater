## YouTube Migrater

A Python tool to automate the migration of liked videos and subscribed channels from an old or deleted YouTube account to a new one, using your Google Takeout MyActivity data.

---

### Features

- **Parse Google Takeout**: Reads `MyActivity.html` to extract watched, liked, and subscribed activities.  
- **Categorize Actions**: Separates activities into likes and subscriptions.  
- **Automate Actions**: Uses the YouTube Data API to re-subscribe to channels and re-like videos on your new account.  
- **Quota Management**: Monitors API usage to stay within daily limits.  
- **Resumable Operations**: Tracks progress in `progress.json` so you can pause and resume without losing your place.  

---

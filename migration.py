import os
import re
import time
import json
import datetime
from bs4 import BeautifulSoup
from typing import Dict, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from tenacity import retry, stop_after_attempt, wait_exponential
from googleapiclient.errors import HttpError


def banner():
    print(r"""
     __     ___   __  __ _                 _            
     \ \   / / | |  \/  (_)               | |           
      \ \_/ /| |_| \  / |_  __ _ _ __ __ _| |_ ___ _ __ 
       \   / | __| |\/| | |/ _` | '__/ _` | __/ _ \ '__|
        | |  | |_| |  | | | (_| | | | (_| | ||  __/ |   
        |_|   \__|_|  |_|_|\__, |_|  \__,_|\__\___|_|   
                            __/ |                       
                           |___/                        
    """)



# ---------------------------
# CONFIGURATION
# ---------------------------
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secret_8393986395-j3meqchdibd4eiijln71944irmlnadn2.apps.googleusercontent.com.json"
TAKEOUT_FILE = "./MyActivity.html"
PROGRESS_FILE = "progress.json"

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_DELAY = 5  # Seconds between API calls
MAX_SUBSCRIPTIONS_PER_RUN = 50  # Conservative default
QUOTA_LIMIT = 10000  # Daily quota limit
QUOTA_COSTS = {
    'channels.list': 1,
    'subscriptions.insert': 50,
    'videos.rate': 1,
    'playlists.insert': 50,
    'playlistItems.insert': 50
}

# ---------------------------
# GLOBAL STATE
# ---------------------------
current_quota = 0
quota_reset_time = datetime.datetime.now() + datetime.timedelta(days=1)

# ---------------------------
# AUTHENTICATION
# ---------------------------
def get_authenticated_service():
    """Authenticate and return YouTube API service instance."""
    global current_quota, quota_reset_time
    
    # Reset quota tracking daily
    if datetime.datetime.now() > quota_reset_time:
        current_quota = 0
        quota_reset_time = datetime.datetime.now() + datetime.timedelta(days=1)
    
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# ---------------------------
# QUOTA MANAGEMENT
# ---------------------------
def check_quota(operation: str) -> bool:
    global current_quota
    cost = QUOTA_COSTS.get(operation, 50)  # Default to 50 if unknown
    
    if current_quota + cost > QUOTA_LIMIT:
        print(f"❌ Quota exhausted! Used: {current_quota}/{QUOTA_LIMIT}")
        print(f"🕒 Quota resets at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return False
    
    current_quota += cost
    return True

# ---------------------------
# TAKEOUT PARSER
# ---------------------------
def parse_takeout_html(file_path: str) -> Dict[str, List]:
    """Parse Google Takeout HTML with enhanced validation."""
    activity = {
        "watched": [],
        "liked": [],
        "subscribed": [],
    }

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f, "lxml")
    except Exception as e:
        print(f"❌ File error: {str(e)}")
        return activity

    entries = soup.find_all("div", class_="content-cell")
    print(f"🔍 Found {len(entries)} activities")

    # Helper functions
    def _is_video_url(url: str):
        return "watch?v=" in url
    def _is_channel_url(url: str):
        return any(p in url for p in ["/channel/", "/c/", "/user/", "/@"])
    def _is_liked(text: str):
        # New: Use regex to allow for leading whitespace and match "liked" at the beginning.
        return re.match(r"^\s*liked\b", text, re.IGNORECASE) is not None
    def _is_sub(text: str):
        return any(p in text for p in ["subscribed to", "subscribed channel"])

    try:
        for i, div in enumerate(entries, 1):
            if i % 10 == 0:
                print(f"⏳ Parsed {i}/{len(entries)} ({i/len(entries):.0%})")
            
            if link := div.find("a", href=True):
                url = link["href"].split('&')[0]
                text = div.get_text(separator=" ", strip=True).lower()
                
                if _is_sub(text) and _is_channel_url(url):
                    activity["subscribed"].append(url)
                elif _is_video_url(url):
                    if _is_liked(text):
                        activity["liked"].append(url)
                    else:
                        activity["watched"].append(url)
                    
        print("✅ Parsing completed")
        return activity
    
    except Exception as e:
        print(f"❌ Parse error: {str(e)}")
        return activity

# ---------------------------
# API OPERATIONS
# ---------------------------
def get_own_channel_id(youtube) -> str:
    """Get authenticated user's channel ID with quota check."""
    if not check_quota('channels.list'):
        raise Exception("Insufficient quota for initial setup")
    
    try:
        response = youtube.channels().list(
            mine=True,
            part="id",
            fields="items/id"
        ).execute()
        return response["items"][0]["id"]
    except HttpError as e:
        if "quotaExceeded" in str(e):
            print("❌ Quota exhausted during initialization")
            raise
        return ""

def is_subscribed(youtube, channel_id: str) -> bool:
    """Check subscription status with proper pagination"""
    try:
        next_page = None
        while True:
            response = youtube.subscriptions().list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=next_page,
                fields="items/snippet/resourceId/channelId,nextPageToken"
            ).execute()
            
            if any(sub["snippet"]["resourceId"]["channelId"] == channel_id 
                   for sub in response.get("items", [])):
                return True
            
            next_page = response.get("nextPageToken")
            if not next_page:
                return False

    except HttpError as e:
        print(f"⚠️ Subscription check failed: {str(e)}")
        return False
    
def get_channel_id(youtube, channel_url: str) -> str:
    """Robust channel ID resolution with URL parsing"""
    # Handle direct channel IDs
    if match := re.search(r"youtube\.com/channel/([\w-]+)", channel_url):
        return match.group(1)
    
    # Handle custom URLs
    if match := re.search(r"youtube\.com/(?:c/|user/|@)([\w-]+)", channel_url):
        username = match.group(1)
        try:
            result = youtube.search().list(
                q=username,
                type="channel",
                part="snippet",
                maxResults=1,
                fields="items/snippet/channelId"
            ).execute()
            return result["items"][0]["snippet"]["channelId"]
        except Exception as e:
            print(f"⚠️ Channel lookup failed for {username}: {str(e)}")
    
    return None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def subscribe_channel(youtube, channel_url: str) -> bool:
    """Improved subscription flow with better error handling"""
    try:
        channel_id = get_channel_id(youtube, channel_url)
        if not channel_id:
            print(f"× Invalid channel URL: {channel_url}")
            return False

        if is_subscribed(youtube, channel_id):
            print(f"⏭️ Already subscribed: {channel_id}")
            return True

        if not check_quota('subscriptions.insert'):
            return False
        
        youtube.subscriptions().insert(
            part="snippet",
            body={
                "snippet": {
                    "resourceId": {
                        "kind": "youtube#channel",
                        "channelId": channel_id
                    }
                }
            }
        ).execute()
        print(f"✓ Subscribed to {channel_id}")
        return True
        
    except HttpError as e:
        if "subscriptionDuplicate" in str(e):
            print(f"⏭️ Already subscribed (API validation): {channel_id}")
            return True
        print(f"× Subscription error: {str(e)}")
        return False

# ---------------------------
# MAIN WORKFLOW
# ---------------------------
def main():
    """Main migration workflow with quota controls."""
    youtube = get_authenticated_service()
    progress = json.load(open(PROGRESS_FILE)) if os.path.exists(PROGRESS_FILE) else {
        "subscriptions": 0, 
        "likes": 0, 
    }

    try:
        # Initial setup
        own_channel_id = get_own_channel_id(youtube)
        activity = parse_takeout_html(TAKEOUT_FILE)
        activity["subscribed"] = [url for url in activity["subscribed"] 
                                  if own_channel_id not in url]

        print(f"\n📊 Migration Targets:")
        print(f"• Subscriptions: {len(activity['subscribed'])}")
        print(f"• Likes: {len(activity['liked'])}")
        print(f"• Watched: {len(activity['watched'])}")

        # Subscription migration
        remaining_subs = len(activity["subscribed"]) - progress["subscriptions"]
        if remaining_subs > 0:
            batch = min(MAX_SUBSCRIPTIONS_PER_RUN, remaining_subs)
            print(f"\n🚀 Processing {batch} subscriptions (quota: {batch * 50} units)")
            
            for url in activity["subscribed"][progress["subscriptions"]:progress["subscriptions"]+batch]:
                if subscribe_channel(youtube, url):
                    progress["subscriptions"] += 1
                    json.dump(progress, open(PROGRESS_FILE, "w"))
                    time.sleep(API_DELAY)

        # Like migration
        remaining_likes = len(activity["liked"]) - progress["likes"]
        if remaining_likes > 0:
            print(f"\n❤️ Processing {remaining_likes} likes (quota: {remaining_likes} units)")
            
            for url in activity["liked"][progress["likes"]:]:
                if check_quota('videos.rate'):
                    youtube.videos().rate(id=url.split("v=")[1], rating="like").execute()
                    progress["likes"] += 1
                    json.dump(progress, open(PROGRESS_FILE, "w"))
                    time.sleep(API_DELAY)

        # Only remove progress file if all migration targets are fully processed
        all_subs_done = progress["subscriptions"] == len(activity["subscribed"])
        all_likes_done = progress["likes"] == len(activity["liked"])

        if all_subs_done and all_likes_done:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            print("\n🎉 Migration completed! All progress has been finalized.")
        else:
            print("\n⏸ Migration incomplete. Progress has been saved for the next run.")

    except KeyboardInterrupt:
        print("\n⏸ Migration paused. Run again to resume.")
        json.dump(progress, open(PROGRESS_FILE, "w"))
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        json.dump(progress, open(PROGRESS_FILE, "w"))

if __name__ == "__main__":
    main()

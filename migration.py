import os
import re
import time
import json
import datetime
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from typing import Dict, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from tenacity import retry, stop_after_attempt, wait_exponential
from googleapiclient.errors import HttpError

# ---------------------------
# CONFIGURATION
# ---------------------------
TOKEN_FILE = os.path.join("data", "token.json")
CREDENTIALS_FILE = "data/client_secret_8393986395-j3meqchdibd4eiijln71944irmlnadn2.apps.googleusercontent.com.json"
TAKEOUT_FILE = "data/MyActivity.html"
PROGRESS_FILE = os.path.join("data", "progress.json")
PARSED_FILE = os.path.join("data", "parsed_activity.json")

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_DELAY = 5  # Seconds between API calls
MAX_SUBSCRIPTIONS_PER_RUN = 50  # Conservative default
QUOTA_LIMIT = 10000  # Daily quota limit (default, may vary per project)


def banner():
    # Define color codes
    ORANGE = "\033[33m"   # Yellow-Orange shade
    RED = "\033[31m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"

    __version__ = "1.0.0"  # Replace with your actual version

    print(rf"""{ORANGE}
{ORANGE}  __     ___   __  __ _                 _  
{ORANGE}  \ \   / / | |  \/  (_)               | |      
{ORANGE}   \ \_/ /| |_| \  / |_  __ _ _ __ __ _| |_ ___ _ __ 
{ORANGE}    \   / | __| |\/| | |/ _` | '__/ _` | __/ _ \ '__|
{ORANGE}     | |  | |_| |  | | | (_| | | | (_| | ||  __/ |
{ORANGE}     |_|   \__|_|  |_|_|\__, |_|  \__,_|\__\___|_|
{ORANGE}                         __/ |           
{ORANGE}                        |___/       {RED}Version : {__version__}

{GREEN}[{WHITE}-{GREEN}]{CYAN} Tool Created by Manomay Bisht {WHITE}{RESET}
    """)

# Example usage
if __name__ == "__main__":
    banner()


def fetch_quota_costs() -> Dict[str, int]:
    url = "https://developers.google.com/youtube/v3/determine_quota_cost"
    headers = {"User-Agent": "ytmig/1.0"}
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        if not soup.find("table"):
            print("⚠️ Quota table not found in the documentation page.")
        
        costs: Dict[str, int] = {}
        current_resource = None

        for row in soup.find("table").select("tbody tr"):
            tds = row.find_all("td")

            # resource cell may contain <h3 id="resourceName"> or be blank (&nbsp;)
            res_td = tds[0]
            h3 = res_td.find("h3")
            if h3:
                # id attribute (gives canonical resource like "channels" or "playlistItems")
                if h3.has_attr("id") and h3["id"].strip():
                    current_resource = h3["id"].strip()
                else:
                    current_resource = re.sub(r"\s+", "", h3.get_text(strip=True))

            method = tds[1].get_text(strip=True)
            cost_text = tds[2].get_text(strip=True)
            m = re.search(r"(\d+)", cost_text)
            if current_resource and m:
                key = f"{current_resource}.{method}"
                costs[key] = int(m.group(1))
            # print("Costs so far:", costs)

        if costs:
            print("Quota costs fetched dynamically from Google Docs.")
            return costs

    except Exception as e:
        print(f"Could not fetch quota costs, falling back to defaults: {e}")

    # fallback hardcoded values
    return {
        "channels.list": 1,
        "subscriptions.insert": 50,
        "videos.rate": 50,
        "playlists.insert": 50,
        "playlistItems.insert": 50,
    }

# Dynamically load quota costs
QUOTA_COSTS = fetch_quota_costs()

# ---------------------------
# GLOBAL STATE
# ---------------------------
current_quota = 0

# Reset happens daily at midnight (local system time).
# Align with Google's Pacific Time reset
def get_next_reset():
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    return datetime.datetime.combine(tomorrow.date(), datetime.time.min)

quota_reset_time = get_next_reset()


# ---------------------------
# QUOTA MANAGEMENT
# ---------------------------
def handle_quota_error(e: Exception, operation: str) -> bool:
    """Centralized quota error handler"""
    if isinstance(e, HttpError) and "quotaExceeded" in str(e):
        print(f"❌ Quota exhausted while performing '{operation}'")
        print(f"🕒 Quota resets at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True  # indicates quota exceeded
    return False

def check_quota(operation: str) -> bool:
    global current_quota, quota_reset_time
    cost = QUOTA_COSTS.get(operation, 50)

    # Reset if needed
    if datetime.datetime.now() > quota_reset_time:
        current_quota = 0
        quota_reset_time = get_next_reset()  # cleaner, reuse your helper

    if current_quota + cost > QUOTA_LIMIT:
        print(f"❌ Local quota exhausted! Used {current_quota}/{QUOTA_LIMIT}")
        print(f"🕒 Quota resets at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return False

    current_quota += cost
    return True

# ---------------------------
# AUTHENTICATION
# ---------------------------
def get_authenticated_service():
    """Authenticate and return YouTube API service instance."""

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        os.makedirs("data", exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# ---------------------------
# TAKEOUT PARSER
# ---------------------------
def parse_takeout_html(file_path: str) -> Dict[str, List]:
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

    # Helper functions
    def _is_video_url(url: str):
        return "watch?v=" in url
    
    def _is_channel_url(url: str):
        return any(p in url for p in ["/channel/", "/c/", "/user/", "/@"])
    
    def _is_liked(text: str):
        return re.match(r"^\s*liked\b", text, re.IGNORECASE) is not None
    
    def _is_sub(text: str):
        return any(p in text for p in ["subscribed to", "subscribed channel"])

    try:
        for div in tqdm(entries, desc="Parsing Takeout", unit=" entry"):  
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
                    
        print("Parsing completed")
        return activity
    
    except Exception as e:
        print(f"Parse error: {str(e)}")
        return activity

# ---------------------------
# API OPERATIONS
# ---------------------------
def get_own_channel_id(youtube) -> str:
    if not check_quota('channels.list'):
        return ""

    try:
        response = youtube.channels().list(
            mine=True,
            part="id",
            fields="items/id"
        ).execute()
        return response["items"][0]["id"]
    except Exception as e:
        if handle_quota_error(e, "channels.list"):
            return ""   # gracefully handled
        print(f"⚠️ Channel fetch failed: {str(e)}")
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

    # Check for numeric channel ID first
    if match := re.search(r"youtube\.com/channel/([\w-]+)", channel_url):
        return match.group(1)

    # Optional: check for @handle (requires API lookup)
    if match := re.search(r"youtube\.com/@([\w-]+)", channel_url):
        handle = match.group(1)
        try:
            result = youtube.search().list(
                q=handle,
                type="channel",
                part="id",
                maxResults=1
            ).execute()
            return result["items"][0]["id"]["channelId"]
        except Exception as e:
            print(f"⚠️ Channel lookup failed for {handle}: {e}")
    
    print(f"⚠️ Unknown channel URL format: {channel_url}")
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def subscribe_channel(youtube, channel_url: str) -> bool:
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
            print(f"Already subscribed (API validation): {channel_id}")
            return True
        print(f"× Subscription error: {str(e)}")
        return False
    
def like_video(youtube, url: str, progress: dict) -> bool:
    if not check_quota('videos.rate'):
        return False
    
    try:
        video_id = url.split("v=")[1]
        youtube.videos().rate(id=video_id, rating="like").execute()
        print(f"✓ Liked video: {video_id}")
        progress["likes"] += 1
        return True

    except HttpError as e:
        if "videoRatingDisabled" in str(e):
            print(f"Skipping video (ratings disabled): {url}")
            progress["links"].append(url)
            return False
        else:
            print(f"x Video Not available {url}")
            print(f"Error liking video {url}: {str(e)}")
            return False
        
def load_or_parse_takeout(parsed_file: str, takeout_file: str) -> Dict[str, List]:

    # Case 1: parsed file exists
    if os.path.exists(parsed_file):
        try:
            existing = json.load(open(parsed_file, "r"))
            if any(existing.values()):   # file has non-empty data
                print("\nParsed file already exists.")
                choice = input("Re-parse Takeout HTML? (Y/N): ").strip().lower()

                if choice == "y":
                    print("\nRe-parsing Takeout...")
                    data = parse_takeout_html(takeout_file)

                    # overwrite old file no matter what
                    json.dump(data, open(parsed_file, "w"), indent=2)
                    return data

                else:
                    print("Using existing parsed file.")
                    return existing

        except Exception:
            print("Error reading existing parsed file. Re-parsing...")
            data = parse_takeout_html(takeout_file)
            json.dump(data, open(parsed_file, "w"), indent=2)
            return data

    # Case 2: parsed file does NOT exist
    print("No parsed file found. Creating new parsed file...")
    data = parse_takeout_html(takeout_file)
    json.dump(data, open(parsed_file, "w"), indent=2)
    return data


# ---------------------------
# MAIN WORKFLOW
# ---------------------------
def main():
    youtube = get_authenticated_service()
    progress = json.load(open(PROGRESS_FILE)) if os.path.exists(PROGRESS_FILE) else {
        "subscriptions": 0, 
        "likes": 0,
        "links": [],
    }

    try:
        # Initial setup
        own_channel_id = get_own_channel_id(youtube)
        if not own_channel_id:
           print("\n⏸ Stopping migration due to quota exhaustion.")
           return   # prevent parsing + wasted work
        
        activity = load_or_parse_takeout(PARSED_FILE, TAKEOUT_FILE)
        activity["subscribed"] = [url for url in activity["subscribed"] 
                                  if own_channel_id not in url]

        print(f"\nMigration Targets:")
        print(f"• Subscriptions: {len(activity['subscribed'])}")
        print(f"• Likes: {len(activity['liked'])}")
        print(f"• Watched: {len(activity['watched'])}")

    
        # ---------------------------
        # Subscription migration
        # ---------------------------

        remaining_subs = len(activity["subscribed"]) - progress["subscriptions"]
        if remaining_subs > 0:
            batch = min(MAX_SUBSCRIPTIONS_PER_RUN, remaining_subs)
            print(f"\nProcessing {batch} subscriptions (est. {batch * QUOTA_COSTS['subscriptions.insert']} quota units)")
            
            for url in activity["subscribed"][progress["subscriptions"]:progress["subscriptions"]+batch]:
                if not check_quota("subscriptions.insert"):
                    print("\n⏸ Quota exhausted during subscriptions. Progress saved.")
                    break

                if subscribe_channel(youtube, url):
                    progress["subscriptions"] += 1
                    json.dump(progress, open(PROGRESS_FILE, "w"))
                    time.sleep(API_DELAY)

        # ---------------------------
        # Likes migration
        # ---------------------------
        remaining_likes = len(activity["liked"]) - progress["likes"]
        if remaining_likes > 0:
            print(f"\nProcessing {remaining_likes} likes (est. {remaining_likes * QUOTA_COSTS['videos.rate']} quota units)")
            
            for url in activity["liked"][progress["likes"]:]:
                if not check_quota("videos.rate"):
                    print("\n⏸ Quota exhausted during likes. Progress saved.")
                    break

                like_video(youtube, url, progress)
                json.dump(progress, open(PROGRESS_FILE, "w"))
                time.sleep(API_DELAY)

        # ---------------------------
        # Finalization
        # ---------------------------
        all_subs_done = progress["subscriptions"] == len(activity["subscribed"])
        all_likes_done = progress["likes"] == len(activity["liked"])

        if all_subs_done and all_likes_done:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            if os.path.exists(PARSED_FILE):
                os.remove(PARSED_FILE)
            print("\n🎉 Migration completed! All progress has been finalized.")
        else:
            print("\n⏸ Migration incomplete. Progress has been saved for the next run.")

    except KeyboardInterrupt:
        print("\n⏸ Migration paused. Run again to resume.")
        json.dump(progress, open(PROGRESS_FILE, "w"))
    except Exception as e:
        if handle_quota_error(e, "main"):
            print("\n⏸ Quota exceeded. Progress saved, please retry after reset.")
        else:
            print(f"\n❌ Fatal error: {str(e)}")
        json.dump(progress, open(PROGRESS_FILE, "w"))



if __name__ == "__main__":
    main()
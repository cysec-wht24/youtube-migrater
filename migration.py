import os
import re
import time
import json
import datetime
import requests
import pytz
from tzlocal import get_localzone
from tqdm import tqdm
from bs4 import BeautifulSoup
from typing import Dict, List
from google.auth.exceptions import RefreshError
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
CREDENTIALS_FILE = "data/client_secret.json"
TAKEOUT_FILE = "data/MyActivity.html"
PROGRESS_FILE = os.path.join("data", "progress.json")
PARSED_FILE = os.path.join("data", "parsed_activity.json")
INFO_FILE = os.path.join("data", "api_derived.json")

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_DELAY = 5  # Seconds between API calls
MAX_SUBSCRIPTIONS_PER_RUN = 100  # Conservative default
QUOTA_LIMIT = 10000  # Daily quota limit (default, may vary per project)

def banner():
    # Define color codes
    ORANGE = "\033[33m"   # Yellow-Orange shade
    RED = "\033[31m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"

    __version__ = "1.0.0"  

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

if __name__ == "__main__":
    banner()


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
# Align with Google's Pacific Time reset
def get_next_reset():

    pacific = pytz.timezone("America/Los_Angeles")
    user_tz = get_localzone()  # auto-detect system timezone

    # Current times
    now_pt = datetime.datetime.now(pacific)
    now_user = datetime.datetime.now(user_tz)

    # Next midnight in Pacific Time
    reset_pt = (now_pt + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Convert to user's timezone
    reset_user = reset_pt.astimezone(user_tz)

    # Safety: ensure it's a future time
    while reset_user <= now_user:
        reset_pt += datetime.timedelta(days=1)
        reset_user = reset_pt.astimezone(user_tz)

    time_left = reset_user - now_user
    return reset_user, time_left

def format_time_left(td):
    total_seconds = int(max(td.total_seconds(), 0))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def fetch_quota_costs() -> Dict[str, int]:
    url = "https://developers.google.com/youtube/v3/determine_quota_cost"
    headers = {"User-Agent": "ytmig/1.0"}
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        if not soup.find("table"):
            print("Quota table not found in the documentation page.")
        
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

# ---------------------------
# GLOBAL STATE
# ---------------------------
QUOTA_COSTS = fetch_quota_costs() # Dynamically load quota costs
current_quota = 0
reset_time, time_left = get_next_reset()
quota_reset_time = reset_time
quota_time_left = time_left

# ---------------------------
# QUOTA MANAGEMENT
# ---------------------------
def handle_quota_error(e: Exception, operation: str) -> bool:
    """Centralized quota error handler"""
    if isinstance(e, HttpError) and "quotaExceeded" in str(e):
        print(f"Quota exhausted while performing '{operation}'")
        print(f"Quota resets in {format_time_left(quota_time_left)} "
              f"at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    return False


def check_quota(operation: str) -> bool:
    global current_quota, quota_reset_time, quota_time_left
    cost = QUOTA_COSTS.get(operation, 50)
    now = datetime.datetime.now(get_localzone())

    # Prevent exceeding local quota
    if current_quota + cost > QUOTA_LIMIT:
        print(f"Local quota exhausted! Used {current_quota}/{QUOTA_LIMIT}")
        print(f"Quota resets in {format_time_left(quota_time_left)} "
              f"at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return False

    # reset logic
    if now > quota_reset_time:
        current_quota = 0
        reset_time, time_left = get_next_reset()
        quota_reset_time = reset_time
        quota_time_left = time_left
    else:
        # recalc remaining time dynamically
        quota_time_left = quota_reset_time - now

    print(f"[Quota] Used: {current_quota}/{QUOTA_LIMIT} | "
          f"Time left: {format_time_left(quota_time_left)}")

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
    
    # If credentials are missing or invalid, handle refresh or re-authentication
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
        except RefreshError:
            print("Token expired or revoked. Re-authenticating...")
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
        print(f"File error: {str(e)}")
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
        print(f"Channel fetch failed: {str(e)}")
        return ""

def load_own_channel_id(info_file: str, youtube) -> str:

    data = {}

    # CASE 1: File exists → load it
    if os.path.exists(info_file):
        try:
            with open(info_file, "r") as f:
                data = json.load(f)

        except (json.JSONDecodeError, OSError):
            print("Error reading info file. Recalling API...")
            channel_id = get_own_channel_id(youtube).strip()
            data["channel_id"] = channel_id
            with open(info_file, "w") as f:
                json.dump(data, f, indent=4)

            return channel_id

        channel_id = data.get("channel_id", "")

        if channel_id:
            print(f"Channel_id already exists: {channel_id}")
            choice = input("Recall API to get channel id? (Y/n): ").strip().lower()
            match choice:
                case "n":
                    print("Using saved channel ID")
                    return channel_id
                case _:
                    print("Recalling API for new channel ID...")
                    channel_id = get_own_channel_id(youtube).strip()
        else:
            print("No channel_id in file. Fetching from API...")
            channel_id = get_own_channel_id(youtube).strip()
    # CASE 2: File does NOT exist
    else:
        print("Info file not found. Fetching from API...")
        channel_id = get_own_channel_id(youtube).strip()

    # Save / Update the file safely
    data["channel_id"] = channel_id
    with open(info_file, "w") as f:
        json.dump(data, f, indent=4)
    return channel_id

def get_subscribed_channel_list(youtube):
    print("Fetching subscriptions from API...")
    subscribed_channel_list = []
    next_page = None
    try:
        while True:
            response = youtube.subscriptions().list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=next_page,
                fields="items/snippet/resourceId/channelId,nextPageToken"
            ).execute()

            for sub in response.get("items", []):
                channel_id = sub["snippet"]["resourceId"]["channelId"]
                subscribed_channel_list.append(channel_id)

            next_page = response.get("nextPageToken")
            if not next_page:
                break

        # Ensure data folder exists
        os.makedirs(os.path.dirname(INFO_FILE), exist_ok=True)
        # Read existing data if file exists
        if os.path.exists(INFO_FILE):
            with open(INFO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # Update JSON
        data["subscribed_channel_list"] = subscribed_channel_list
        with open(INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Saved {len(subscribed_channel_list)} channels into {INFO_FILE}")
        return subscribed_channel_list

    except HttpError as e:
        print(f"Subscription fetch failed: {e}")
        return []

def is_subscribed(youtube, channel_id: str) -> bool:
    # If file does not exist, create it with fresh subscriptions
    if not os.path.exists(INFO_FILE):
        print("api_derived.json does not exist. Creating it now...")
        subscribed_list = get_subscribed_channel_list(youtube)
    else:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # If key missing or empty, refetch
        if "subscribed_channel_list" not in data or not data["subscribed_channel_list"]:
            print("Subscription list missing or empty. Rebuilding...")
            subscribed_list = get_subscribed_channel_list(youtube)
        else:
            subscribed_list = data["subscribed_channel_list"]

    # Now compare locally
    if channel_id in subscribed_list:
        return True
    else:
        return False

def get_channel_id(youtube, channel_url: str) -> str:

    # Check for numeric channel ID first
    if match := re.search(r"youtube\.com/channel/([\w-]+)", channel_url):
        return match.group(1)

    # Optional: check for @handle (requires API lookup) Not used
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
            print(f"Channel lookup failed for {handle}: {e}")
    
    print(f"Unknown channel URL format: {channel_url}")
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def subscribe_channel(youtube, channel_url: str) -> bool:
    try:
        channel_id = get_channel_id(youtube, channel_url)
        if not channel_id:
            print(f"× Invalid channel URL: {channel_url}")
            return False

        if is_subscribed(youtube, channel_id):
            print(f"⏭ Already subscribed: {channel_id}")
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
        

# ---------------------------
# MAIN WORKFLOW
# ---------------------------
def main():
    youtube = get_authenticated_service()
    # print("youtube is ready")
    progress = json.load(open(PROGRESS_FILE)) if os.path.exists(PROGRESS_FILE) else {
        "subscriptions": 0, 
        "likes": 0,
        "links": [],
    }

    try:
        # Initial setup
        own_channel_id = load_own_channel_id(INFO_FILE, youtube)
        # print(own_channel_id)
        if not own_channel_id:
           print("\n⏸ Stopping migration due to quota exhaustion.")
           return   # prevent parsing + wasted work
        choice = input("Have you subscribed to channels on youtube recently ? (Y/N)").strip().lower()
        match choice:
            case "n":
                pass
            case _:
                get_subscribed_channel_list(youtube)

        activity = load_or_parse_takeout(PARSED_FILE, TAKEOUT_FILE)
        activity["subscribed"] = [url for url in activity["subscribed"] if own_channel_id not in url]
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
            print("\n Migration completed! All progress has been finalized.")
        else:
            print("\n⏸ Migration incomplete. Progress has been saved for the next run.")

    except KeyboardInterrupt:
        print("\n⏸ Migration paused. Run again to resume.")
        json.dump(progress, open(PROGRESS_FILE, "w"))
    except Exception as e:
        if handle_quota_error(e, "main"):
            print("\n⏸ Quota exceeded. Progress saved, please retry after reset.")
        else:
            print(f"\nFatal error: {str(e)}")
        json.dump(progress, open(PROGRESS_FILE, "w"))

if __name__ == "__main__":
    main()
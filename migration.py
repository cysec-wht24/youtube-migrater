import os
import re
import time
import json
import datetime
import requests
import pytz
import csv
from pathlib import Path
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
MAX_SUBSCRIPTIONS_PER_RUN = 50  # Conservative default
MAX_LIKES_PER_RUN = 100
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
        current_left = quota_reset_time - datetime.datetime.now(get_localzone())
        print(f"Quota resets in {format_time_left(current_left)} "
              f"at {quota_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    return False

# ---------------------------
# AUTHENTICATION
# ---------------------------
def get_authenticated_service():
    """Authenticate and return YouTube API service instance."""

    IS_DOCKER = os.path.exists("/.dockerenv")

    def _run_flow(credentials_file):
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)

        if IS_DOCKER:
            return flow.run_local_server(host="0.0.0.0", port=8080)
        else:
            return flow.run_local_server(port=0)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If credentials are missing or invalid, handle refresh or re-authentication
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = _run_flow(CREDENTIALS_FILE)
        except RefreshError:
            print("Token expired or revoked. Re-authenticating...")
            creds = _run_flow(CREDENTIALS_FILE)

        os.makedirs("data", exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# ---------------------------
# FILE DETECTION
# ---------------------------
def detect_available_files() -> Dict[str, List[str]]:
    """Detect available HTML and CSV files in data directory"""
    data_dir = Path("data")
    files = {"html": [], "csv": []}
    
    if not data_dir.exists():
        return files
    
    for file in data_dir.iterdir():
        if file.is_file():
            if file.suffix.lower() == ".html":
                files["html"].append(file.name)
            elif file.suffix.lower() == ".csv":
                files["csv"].append(file.name)
    
    return files

# ---------------------------
# CSV PARSERS
# ---------------------------
def parse_subscriptions_csv(file_path: str) -> List[str]:
    """Parse subscriptions.csv and return list of channel URLs"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use Channel URL if available, otherwise construct from Channel ID
                if 'Channel URL' in row and row['Channel URL'].strip():
                    urls.append(row['Channel URL'].strip())
                elif 'Channel ID' in row and row['Channel ID'].strip():
                    urls.append(f"https://www.youtube.com/channel/{row['Channel ID'].strip()}")
    except Exception as e:
        print(f"Error parsing subscriptions CSV: {e}")
    
    return urls

def parse_music_library_csv(file_path: str) -> List[str]:
    """Parse music library CSV and return list of video URLs"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Video ID' in row and row['Video ID'].strip():
                    video_id = row['Video ID'].strip()
                    urls.append(f"https://www.youtube.com/watch?v={video_id}")
    except Exception as e:
        print(f"Error parsing music library CSV: {e}")
    
    return urls

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

def merge_activity_data(existing: Dict[str, List], new: Dict[str, List]) -> Dict[str, List]:
    """Merge new activity data into existing, removing duplicates"""
    merged = {
        "watched": list(set(existing.get("watched", []) + new.get("watched", []))),
        "liked": list(set(existing.get("liked", []) + new.get("liked", []))),
        "subscribed": list(set(existing.get("subscribed", []) + new.get("subscribed", []))),
    }
    return merged

def load_or_parse_takeout(parsed_file: str, data_dir: str = "data") -> Dict[str, List]:
    """Interactive file selection and parsing"""
    
    # Check if parsed file exists
    existing_data = {"watched": [], "liked": [], "subscribed": []}
    if os.path.exists(parsed_file):
        try:
            existing_data = json.load(open(parsed_file, "r"))
            if any(existing_data.values()):
                print("\nParsed file already exists with data.")
        except Exception:
            print("Error reading existing parsed file.")
    
    # Detect available files
    available = detect_available_files()
    
    if not available["html"] and not available["csv"]:
        print("\nNo HTML or CSV files found in data directory!")
        return existing_data
    
    # Display detected files
    print("\nDetected files:")
    all_files = []
    for html_file in available["html"]:
        print(f"  • {html_file}")
        all_files.append(("html", html_file))
    for csv_file in available["csv"]:
        print(f"  • {csv_file}")
        all_files.append(("csv", csv_file))
    
    # Ask user what to do
    if any(existing_data.values()):
        choice = input("\nOptions:\n1) Use existing parsed_activity.json\n2) Parse new file(s)\nEnter choice (1/2): ").strip()
        if choice == "1":
            print("Using existing parsed file.")
            return existing_data
    
    # Let user select file to parse
    print("\nEnter filename to parse (or press Enter to skip): ")
    filename = input("Filename: ").strip()
    
    if not filename:
        return existing_data
    
    # Find and parse the selected file
    file_path = os.path.join(data_dir, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {filename}")
        return existing_data
    
    new_data = {"watched": [], "liked": [], "subscribed": []}
    
    # Parse based on file type
    if filename.endswith(".html"):
        print(f"\nParsing HTML file: {filename}")
        new_data = parse_takeout_html(file_path)
    
    elif filename.lower() == "subscriptions.csv":
        print(f"\nParsing subscriptions CSV: {filename}")
        new_data["subscribed"] = parse_subscriptions_csv(file_path)
        print(f"Found {len(new_data['subscribed'])} subscriptions")
    
    elif "music" in filename.lower() and filename.endswith(".csv"):
        print(f"\nParsing music library CSV: {filename}")
        new_data["liked"] = parse_music_library_csv(file_path)
        print(f"Found {len(new_data['liked'])} liked videos")
    
    else:
        print(f"Unknown file format: {filename}")
        return existing_data
    
    # Merge with existing data
    merged_data = merge_activity_data(existing_data, new_data)
    
    # Save merged data
    json.dump(merged_data, open(parsed_file, "w"), indent=2)
    print(f"\nData merged and saved to {parsed_file}")
    
    return merged_data

# ---------------------------
# API OPERATIONS
# ---------------------------
def get_own_channel_id(youtube) -> str:

    try:
        response = youtube.channels().list(
            mine=True,
            part="id",
            fields="items/id"
        ).execute()
        return response["items"][0]["id"]
    except Exception as e:
        print(f"× Channel fetch failed (unexpected error): {str(e)}")
        return ""
    except HttpError as e:
        err = str(e)
        if handle_quota_error(e, "channels.list"):
            raise e  # bubble up to main() to stop

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
        err = str(e)
        if handle_quota_error(e, "subscriptions.list"):
            raise e
        print(f"× Subscription fetch failed (HTTP error): {err}")
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

    # Compare locally
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


# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def subscribe_channel(youtube, channel_url: str) -> bool:
    try:
        channel_id = get_channel_id(youtube, channel_url)
        if not channel_id:
            print(f"× Invalid channel URL: {channel_url}")
            return False

        if is_subscribed(youtube, channel_id):
            print(f"★ Already subscribed: {channel_id}")
            return True
        
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
        err = str(e)
        if handle_quota_error(e, "subscriptions.insert"):
            raise e
        if "subscriptionDuplicate" in err:
            print(f"Already subscribed (API validation): {channel_id}")
            return True
        if "publisherNotFound" in err:
            print(f"× Channel not found: {channel_id}")
            return False
        print(f"× Subscription error: {err}")
        return False
    

def like_video(youtube, url: str, progress: dict) -> bool:
    try:
        video_id = url.split("v=")[1]
        youtube.videos().rate(id=video_id, rating="like").execute()
        print(f"✓ Liked video: {video_id}")
        progress["likes"] += 1
        return True

    except HttpError as e:
        err = str(e)
        if handle_quota_error(e, "videos.rate"): # return False but signal main() to stop
            raise e
        if "videoRatingDisabled" in err:
            print(f"Skipping video (Do manually) (auto ratings disabled): {url}")
            progress["links"].append(url)
            return False
        if "notFound" in err:
            print(f"x Video Not available {url}")
            return False
        else:
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

        activity = load_or_parse_takeout(PARSED_FILE)
        activity["subscribed"] = [url for url in activity["subscribed"] if own_channel_id not in url]
        print(f"\nMigration Targets:")
        print(f"• Subscriptions: {len(activity['subscribed'])}")
        print(f"• Likes: {len(activity['liked'])}")
        print(f"• Watched: {len(activity['watched'])}")

        # ---------------------------
        # USER CONTROL
        # ---------------------------
        print("\nChoose what to run:")
        print("1) Run only Likes")
        print("2) Run only Subscriptions")
        print("3) Run Likes then Subscriptions")
        print("4) Run Subscriptions then Likes")

        order = input("Enter choice (1/2/3/4): ").strip()

        likes_limit = input("Max likes to process this run? (Press Enter for ALL): ").strip()
        subs_limit = input("Max subscriptions to process this run? (Press Enter for ALL): ").strip()

        likes_limit = int(likes_limit) if likes_limit.isdigit() else MAX_LIKES_PER_RUN
        subs_limit = int(subs_limit) if subs_limit.isdigit() else MAX_SUBSCRIPTIONS_PER_RUN

    
        # ---------------------------
        # Subscription migration
        # ---------------------------
        def process_subscriptions():
            remaining_subs = len(activity["subscribed"]) - progress["subscriptions"]

            if remaining_subs > 0:
                batch = min(subs_limit, remaining_subs)
                print(f"\nProcessing {batch} subscriptions (est. {batch * QUOTA_COSTS['subscriptions.insert']} quota units)")

                for url in activity["subscribed"][progress["subscriptions"]:progress["subscriptions"] + batch]:
                    if subscribe_channel(youtube, url):
                        progress["subscriptions"] += 1
                        json.dump(progress, open(PROGRESS_FILE, "w"))
                        time.sleep(API_DELAY)

        # ---------------------------
        # Likes migration
        # ---------------------------
        def process_likes():
            remaining_likes = len(activity["liked"]) - progress["likes"]

            if remaining_likes > 0:
                batch = min(likes_limit, remaining_likes)
                print(f"\nProcessing {batch} likes (est. {batch * QUOTA_COSTS['videos.rate']} quota units)")

                for url in activity["liked"][progress["likes"]:progress["likes"] + batch]:
                    like_video(youtube, url, progress)
                    progress["likes"] += 1
                    json.dump(progress, open(PROGRESS_FILE, "w"))
                    time.sleep(API_DELAY)

        # ---------------------------
        # Execute based on user choice
        # ---------------------------
        if order == "1":
            process_likes()

        elif order == "2":
            process_subscriptions()

        elif order == "3":
            process_likes()
            process_subscriptions()

        elif order == "4":
            process_subscriptions()
            process_likes()

        else:
            print("Invalid choice! Defaulting to Likes then Subscriptions.")
            process_subscriptions()
            process_likes()

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
            print("\n✓ Migration completed! All progress has been finalized.")
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
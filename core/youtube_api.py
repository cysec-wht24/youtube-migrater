"""
YouTube API functions - Pure logic, no GUI dependencies
All functions return values or raise exceptions
Logging is handled by the caller (MigrationWorker)
"""

import os
import re
import json
import requests
import datetime
import pytz
from tzlocal import get_localzone
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

# ---------------------------
# CONSTANTS
# ---------------------------
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def get_next_reset() -> Tuple[datetime.datetime, datetime.timedelta]:
    """Calculate next quota reset time (Pacific midnight)"""
    pacific = pytz.timezone("America/Los_Angeles")
    user_tz = get_localzone()
    
    now_pt = datetime.datetime.now(pacific)
    now_user = datetime.datetime.now(user_tz)
    
    reset_pt = (now_pt + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    reset_user = reset_pt.astimezone(user_tz)
    
    while reset_user <= now_user:
        reset_pt += datetime.timedelta(days=1)
        reset_user = reset_pt.astimezone(user_tz)
    
    time_left = reset_user - now_user
    return reset_user, time_left


def format_time_left(td: datetime.timedelta) -> str:
    """Format timedelta as HH:MM:SS"""
    total_seconds = int(max(td.total_seconds(), 0))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def fetch_quota_costs() -> Dict[str, int]:
    """Fetch quota costs from Google documentation"""
    url = "https://developers.google.com/youtube/v3/determine_quota_cost"
    headers = {"User-Agent": "ytmig/1.0"}
    
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        if not soup.find("table"):
            return {}
        
        costs: Dict[str, int] = {}
        current_resource = None
        
        for row in soup.find("table").select("tbody tr"):
            tds = row.find_all("td")
            res_td = tds[0]
            h3 = res_td.find("h3")
            
            if h3:
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
        
        return costs if costs else {}
        
    except Exception:
        # Fallback to hardcoded values
        return {
            "channels.list": 1,
            "subscriptions.insert": 50,
            "videos.rate": 50,
            "playlists.insert": 50,
            "playlistItems.insert": 50,
        }


def is_quota_error(e: Exception) -> bool:
    """Check if exception is a quota error"""
    return isinstance(e, HttpError) and "quotaExceeded" in str(e)


# ---------------------------
# AUTHENTICATION
# ---------------------------
def get_authenticated_service(credentials_file: str, token_file: str):
    """Authenticate and return YouTube API service instance"""
    creds = None
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
        except RefreshError:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)


# ---------------------------
# TAKEOUT PARSER
# ---------------------------
def parse_takeout_html(file_path: str, progress_callback=None) -> Dict[str, List]:
    """
    Parse YouTube Takeout HTML file
    progress_callback: optional function(current, total) for progress updates
    """
    activity = {
        "watched": [],
        "liked": [],
        "subscribed": [],
    }
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f, "lxml")
    except Exception as e:
        raise Exception(f"File error: {str(e)}")
    
    entries = soup.find_all("div", class_="content-cell")
    total = len(entries)
    
    def _is_video_url(url: str):
        return "watch?v=" in url
    
    def _is_channel_url(url: str):
        return any(p in url for p in ["/channel/", "/c/", "/user/", "/@"])
    
    def _is_liked(text: str):
        return re.match(r"^\s*liked\b", text, re.IGNORECASE) is not None
    
    def _is_sub(text: str):
        return any(p in text for p in ["subscribed to", "subscribed channel"])
    
    try:
        for idx, div in enumerate(entries):
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
            
            # Report progress every 100 entries
            if progress_callback and (idx % 100 == 0 or idx == total - 1):
                progress_callback(idx + 1, total)
        
        return activity
        
    except Exception as e:
        raise Exception(f"Parse error: {str(e)}")


# ---------------------------
# API OPERATIONS
# ---------------------------
def get_own_channel_id(youtube) -> str:
    """Get authenticated user's channel ID"""
    response = youtube.channels().list(
        mine=True,
        part="id",
        fields="items/id"
    ).execute()
    
    if "items" in response and len(response["items"]) > 0:
        return response["items"][0]["id"]
    return ""


def get_subscribed_channel_list(youtube, info_file: str) -> List[str]:
    """Fetch all subscribed channels and save to info_file"""
    subscribed_channel_list = []
    next_page = None
    
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
    
    # Save to file
    os.makedirs(os.path.dirname(info_file), exist_ok=True)
    
    if os.path.exists(info_file):
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    
    data["subscribed_channel_list"] = subscribed_channel_list
    
    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    return subscribed_channel_list


def is_subscribed(youtube, channel_id: str, info_file: str) -> bool:
    """Check if already subscribed to a channel (uses local cache)"""
    if not os.path.exists(info_file):
        subscribed_list = get_subscribed_channel_list(youtube, info_file)
    else:
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "subscribed_channel_list" not in data or not data["subscribed_channel_list"]:
            subscribed_list = get_subscribed_channel_list(youtube, info_file)
        else:
            subscribed_list = data["subscribed_channel_list"]
    
    return channel_id in subscribed_list


def get_channel_id(youtube, channel_url: str) -> Optional[str]:
    """Extract channel ID from URL"""
    # Direct channel ID
    if match := re.search(r"youtube\.com/channel/([\w-]+)", channel_url):
        return match.group(1)
    
    # Handle @username (requires API lookup)
    if match := re.search(r"youtube\.com/@([\w-]+)", channel_url):
        handle = match.group(1)
        try:
            result = youtube.search().list(
                q=handle,
                type="channel",
                part="id",
                maxResults=1
            ).execute()
            if "items" in result and len(result["items"]) > 0:
                return result["items"][0]["id"]["channelId"]
        except Exception:
            pass
    
    return None


def subscribe_channel(youtube, channel_url: str, info_file: str) -> Tuple[bool, str]:
    """
    Subscribe to a channel
    Returns: (success: bool, message: str)
    """
    channel_id = get_channel_id(youtube, channel_url)
    if not channel_id:
        return False, f"Invalid channel URL: {channel_url}"
    
    if is_subscribed(youtube, channel_id, info_file):
        return True, f"Already subscribed: {channel_id}"
    
    try:
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
        return True, f"Subscribed to {channel_id}"
        
    except HttpError as e:
        err = str(e)
        if "subscriptionDuplicate" in err:
            return True, f"Already subscribed (API validation): {channel_id}"
        if "publisherNotFound" in err:
            return False, f"Channel not found: {channel_id}"
        if is_quota_error(e):
            raise  # Re-raise quota errors
        return False, f"Subscription error: {err}"


def like_video(youtube, url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Like a video
    Returns: (success: bool, message: str, video_url_if_manual: Optional[str])
    """
    try:
        video_id = url.split("v=")[1].split("&")[0]
        youtube.videos().rate(id=video_id, rating="like").execute()
        return True, f"Liked video: {video_id}", None
        
    except HttpError as e:
        err = str(e)
        if "videoRatingDisabled" in err:
            return False, f"Skipping (ratings disabled): {url}", url
        if "notFound" in err:
            return False, f"Video not available: {url}", None
        if is_quota_error(e):
            raise  # Re-raise quota errors
        return False, f"Error liking video: {err}", None
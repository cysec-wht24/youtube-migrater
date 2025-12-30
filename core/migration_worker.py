"""
Migration Worker - Runs in background thread
Emits signals to update GUI, reads config from data/config.json
"""

import os
import json
import datetime
from PySide6.QtCore import QObject, Signal, QThread
from typing import Dict, List

from .youtube_api import (
    get_authenticated_service,
    parse_takeout_html,
    get_own_channel_id,
    get_subscribed_channel_list,
    subscribe_channel,
    like_video,
    fetch_quota_costs,
    get_next_reset,
    format_time_left,
    is_quota_error,
)


class MigrationWorker(QObject):
    """
    Worker that performs YouTube migration in background
    Communicates with GUI via signals
    """
    
    # Signals
    log_message = Signal(str)  # Emit log messages
    progress_updated = Signal(int, int, str)  # current, total, operation_type
    finished = Signal()  # Migration completed
    error_occurred = Signal(str)  # Fatal error
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
        self.config = {}
        self.youtube = None
        self.quota_costs = {}
        self.quota_reset_time = None
    
    def stop(self):
        """Request worker to stop"""
        self.should_stop = True
        self.log_message.emit("⏸ Stop requested by user...")
    
    def load_config(self) -> Dict:
        """Load configuration from data/config.json"""
        config_path = "data/config.json"
        
        if not os.path.exists(config_path):
            raise FileNotFoundError("Configuration file not found: data/config.json")
        
        with open(config_path, "r") as f:
            return json.load(f)
    
    def run(self):
        """Main migration workflow - runs in background thread"""
        try:
            # Load configuration
            self.log_message.emit("Loading configuration...")
            self.config = self.load_config()
            
            # Fetch quota costs
            self.log_message.emit("Fetching quota costs...")
            self.quota_costs = fetch_quota_costs()
            if self.quota_costs:
                self.log_message.emit("✓ Quota costs fetched from Google Docs")
            else:
                self.log_message.emit("⚠ Using default quota costs")
            
            # Calculate quota reset time
            reset_time, time_left = get_next_reset()
            self.quota_reset_time = reset_time
            self.log_message.emit(f"Quota resets in {format_time_left(time_left)} at {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check stop flag
            if self.should_stop:
                self.log_message.emit("⏸ Migration stopped before starting")
                self.finished.emit()
                return
            
            # Authenticate with YouTube API
            self.log_message.emit("Authenticating with YouTube API...")
            self.youtube = get_authenticated_service(
                self.config.get("client_secret_path", "data/client_secret.json"),
                "data/token.json"
            )
            self.log_message.emit("✓ Authentication successful")
            
            # Get own channel ID
            self.log_message.emit("Fetching your channel ID...")
            own_channel_id = self._load_own_channel_id()
            if not own_channel_id:
                self.error_occurred.emit("Failed to fetch channel ID")
                return
            self.log_message.emit(f"✓ Channel ID: {own_channel_id}")
            
            # Refresh subscriptions if requested
            if self.config.get("refresh_subscriptions", False):
                self.log_message.emit("Refreshing subscription list...")
                get_subscribed_channel_list(self.youtube, "data/api_derived.json")
                self.log_message.emit("✓ Subscription list updated")
            
            # Check stop flag
            if self.should_stop:
                self.finished.emit()
                return
            
            # Parse or load activity data
            self.log_message.emit("Loading activity data...")
            activity = self._load_or_parse_takeout()
            
            # Filter out own channel from subscriptions
            activity["subscribed"] = [
                url for url in activity["subscribed"] 
                if own_channel_id not in url
            ]
            
            self.log_message.emit(f"\n📊 Migration Targets:")
            self.log_message.emit(f"   • Subscriptions: {len(activity['subscribed'])}")
            self.log_message.emit(f"   • Likes: {len(activity['liked'])}")
            self.log_message.emit(f"   • Watched: {len(activity['watched'])}")
            
            # Check stop flag
            if self.should_stop:
                self.finished.emit()
                return
            
            # Load progress
            progress = self._load_progress()
            
            # Get run mode from config
            run_mode = self.config.get("run_mode", "likes_then_subs")
            
            # Execute migration based on run mode
            if run_mode == "only_likes":
                self._process_likes(activity, progress)
            
            elif run_mode == "only_subscriptions":
                self._process_subscriptions(activity, progress)
            
            elif run_mode == "likes_then_subs":
                self._process_likes(activity, progress)
                if not self.should_stop:
                    self._process_subscriptions(activity, progress)
            
            elif run_mode == "subs_then_likes":
                self._process_subscriptions(activity, progress)
                if not self.should_stop:
                    self._process_likes(activity, progress)
            
            # Check if migration is complete
            all_subs_done = progress["subscriptions"] >= len(activity["subscribed"])
            all_likes_done = progress["likes"] >= len(activity["liked"])
            
            if all_subs_done and all_likes_done:
                self._cleanup_files()
                self.log_message.emit("\n✓ Migration completed! All progress finalized.")
            else:
                self.log_message.emit("\n⏸ Migration incomplete. Progress saved for next run.")
            
            self.finished.emit()
            
        except Exception as e:
            if is_quota_error(e):
                self.log_message.emit("\n⏸ Quota exceeded. Progress saved.")
                current_left = self.quota_reset_time - datetime.datetime.now()
                self.log_message.emit(f"Quota resets in {format_time_left(current_left)}")
            else:
                self.error_occurred.emit(f"Fatal error: {str(e)}")
            
            # Save progress on error
            self._save_progress(self._load_progress())
            self.finished.emit()
    
    def _load_own_channel_id(self) -> str:
        """Load or fetch own channel ID"""
        info_file = "data/api_derived.json"
        data = {}
        
        if os.path.exists(info_file):
            try:
                with open(info_file, "r") as f:
                    data = json.load(f)
                channel_id = data.get("channel_id", "")
                
                if channel_id:
                    # Use existing unless config says to refresh
                    if not self.config.get("refresh_channel_id", False):
                        return channel_id
            except Exception:
                pass
        
        # Fetch from API
        channel_id = get_own_channel_id(self.youtube)
        data["channel_id"] = channel_id
        
        os.makedirs("data", exist_ok=True)
        with open(info_file, "w") as f:
            json.dump(data, f, indent=4)
        
        return channel_id
    
    def _load_or_parse_takeout(self) -> Dict[str, List]:
        """Load existing parsed data or parse new takeout file"""
        parsed_file = "data/parsed_activity.json"
        takeout_file = self.config.get("html_takeout_path", "data/MyActivity.html")
        
        # Check if parsed file exists
        if os.path.exists(parsed_file):
            try:
                with open(parsed_file, "r") as f:
                    existing = json.load(f)
                
                # If reparse is requested or parsed file is empty
                if self.config.get("reparse_takeout", False) or not any(existing.values()):
                    self.log_message.emit("Re-parsing Takeout HTML...")
                    data = self._parse_with_progress(takeout_file)
                    with open(parsed_file, "w") as f:
                        json.dump(data, f, indent=2)
                    return data
                else:
                    self.log_message.emit("✓ Using existing parsed data")
                    return existing
            
            except Exception:
                self.log_message.emit("⚠ Error reading parsed file. Re-parsing...")
                data = self._parse_with_progress(takeout_file)
                with open(parsed_file, "w") as f:
                    json.dump(data, f, indent=2)
                return data
        
        # No parsed file exists
        self.log_message.emit("No parsed file found. Parsing Takeout HTML...")
        data = self._parse_with_progress(takeout_file)
        
        os.makedirs("data", exist_ok=True)
        with open(parsed_file, "w") as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def _parse_with_progress(self, file_path: str) -> Dict[str, List]:
        """Parse with progress updates"""
        def progress_callback(current, total):
            self.progress_updated.emit(current, total, "parsing")
        
        return parse_takeout_html(file_path, progress_callback)
    
    def _load_progress(self) -> Dict:
        """Load migration progress"""
        progress_file = "data/progress.json"
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "subscriptions": 0,
            "likes": 0,
            "links": [],
        }
    
    def _save_progress(self, progress: Dict):
        """Save migration progress"""
        os.makedirs("data", exist_ok=True)
        with open("data/progress.json", "w") as f:
            json.dump(progress, f, indent=2)
    
    def _process_subscriptions(self, activity: Dict, progress: Dict):
        """Process subscription migration"""
        remaining = len(activity["subscribed"]) - progress["subscriptions"]
        
        if remaining <= 0:
            self.log_message.emit("✓ All subscriptions already processed")
            return
        
        max_subs = self.config.get("max_subscriptions", 50)
        batch = min(max_subs, remaining)
        
        cost_per_sub = self.quota_costs.get("subscriptions.insert", 50)
        self.log_message.emit(f"\n🔔 Processing {batch} subscriptions (est. {batch * cost_per_sub} quota units)")
        
        start_idx = progress["subscriptions"]
        end_idx = start_idx + batch
        
        for idx, url in enumerate(activity["subscribed"][start_idx:end_idx]):
            if self.should_stop:
                self.log_message.emit("⏸ Subscription processing stopped")
                break
            
            try:
                success, message = subscribe_channel(self.youtube, url, "data/api_derived.json")
                self.log_message.emit(f"{'✓' if success else '✗'} {message}")
                
                if success:
                    progress["subscriptions"] += 1
                    self._save_progress(progress)
                    self.progress_updated.emit(
                        progress["subscriptions"],
                        len(activity["subscribed"]),
                        "subscriptions"
                    )
                
                # Delay between API calls
                QThread.msleep(self.config.get("api_delay", 5) * 1000)
                
            except Exception as e:
                if is_quota_error(e):
                    raise  # Bubble up quota errors
                self.log_message.emit(f"✗ Error: {str(e)}")
    
    def _process_likes(self, activity: Dict, progress: Dict):
        """Process likes migration"""
        remaining = len(activity["liked"]) - progress["likes"]
        
        if remaining <= 0:
            self.log_message.emit("✓ All likes already processed")
            return
        
        max_likes = self.config.get("max_likes", 100)
        batch = min(max_likes, remaining)
        
        cost_per_like = self.quota_costs.get("videos.rate", 50)
        self.log_message.emit(f"\n❤️ Processing {batch} likes (est. {batch * cost_per_like} quota units)")
        
        start_idx = progress["likes"]
        end_idx = start_idx + batch
        
        for idx, url in enumerate(activity["liked"][start_idx:end_idx]):
            if self.should_stop:
                self.log_message.emit("⏸ Likes processing stopped")
                break
            
            try:
                success, message, manual_url = like_video(self.youtube, url)
                self.log_message.emit(f"{'✓' if success else '✗'} {message}")
                
                if manual_url:
                    progress["links"].append(manual_url)
                
                progress["likes"] += 1
                self._save_progress(progress)
                self.progress_updated.emit(
                    progress["likes"],
                    len(activity["liked"]),
                    "likes"
                )
                
                # Delay between API calls
                QThread.msleep(self.config.get("api_delay", 5) * 1000)
                
            except Exception as e:
                if is_quota_error(e):
                    raise  # Bubble up quota errors
                self.log_message.emit(f"✗ Error: {str(e)}")
    
    def _cleanup_files(self):
        """Clean up temporary files after successful completion"""
        files_to_remove = ["data/progress.json", "data/parsed_activity.json"]
        
        for file in files_to_remove:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    self.log_message.emit(f"✓ Cleaned up: {file}")
                except Exception as e:
                    self.log_message.emit(f"⚠ Could not remove {file}: {e}")


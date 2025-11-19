import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from collections import OrderedDict

# try to import tqdm, but keep parser usable if tqdm isn't installed
try:
    from tqdm import tqdm
except Exception:
    tqdm = None  # type: ignore

YOUTUBE_BASE = "https://www.youtube.com"

def _normalize_href(href: str) -> str:
    """Normalize href: handle relative URLs and strip query params after the video id where appropriate."""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = YOUTUBE_BASE + href
    return href

def _first_preferred_link(div) -> Optional[str]:
    """
    Return the *best* link from the content-cell div:
    - Prefer video links (watch?v= or /watch? or music.youtube.com/watch)
    - Else prefer channel links (/channel/, /c/, /user/, /@)
    - Else return the first absolute link
    """
    anchors = [a for a in div.find_all("a", href=True)]
    if not anchors:
        return None

    # Normalize hrefs and keep pairs (href, anchor)
    hrefs = [(a["href"].strip(), a) for a in anchors]

    # prefer video links
    for href, _ in hrefs:
        if "watch?v=" in href or "music.youtube.com/watch" in href or "/watch?" in href:
            return _normalize_href(href.split("&")[0])

    # prefer channel links
    for href, _ in hrefs:
        if any(p in href for p in ["/channel/", "/c/", "/user/", "/@"]):
            return _normalize_href(href.split("&")[0])

    # fallback to first link (normalized)
    href = hrefs[0][0]
    return _normalize_href(href.split("&")[0])

def parse_takeout_html(file_path: str) -> Dict[str, List[str]]:
    """
    Parse a Google Takeout activity HTML (YouTube) and return dict with lists:
      { "watched": [...video urls...],
        "liked":  [...video urls...],
        "subscribed": [...channel urls...] }
    """
    activity = {"watched": [], "liked": [], "subscribed": []}

    # Load HTML
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            soup = BeautifulSoup(fh, "lxml")
    except Exception as e:
        print(f"❌ File read error: {e}")
        return activity

    entries = soup.find_all("div", class_="content-cell")
    if not entries:
        print("⚠️ No content-cell entries found in the file. Is this the correct Takeout HTML?")
        return activity

    # helpers
    def is_video_link(url: str) -> bool:
        if not url:
            return False
        url = url.lower()
        return ("watch?v=" in url) or ("music.youtube.com/watch" in url) or ("/watch?" in url)

    def is_channel_link(url: str) -> bool:
        if not url:
            return False
        return any(p in url for p in ["/channel/", "/c/", "/user/", "/@"])

    # robust liked detection: starts with "Liked" (allow whitespace and NBSP)
    def is_liked_text(text: str) -> bool:
        if not text:
            return False
        # replace NBSP with regular space, collapse leading whitespace
        t = text.replace("\xa0", " ").lstrip()
        return re.match(r"(?i)^liked\b", t) is not None  # case-insensitive

    # maintain order and uniqueness
    def add_unique(lst: List[str], value: str):
        if not value:
            return
        if value not in lst:
            lst.append(value)

    # iterate with tqdm if available
    iterator = tqdm(entries, desc="📄 Parsing Takeout", unit="entry") if tqdm else entries

    for div in iterator:
        # choose best link in div
        best = _first_preferred_link(div)
        if not best:
            continue

        # compute text to test (lowercase, collapse whitespace)
        raw_text = div.get_text(separator=" ", strip=True)
        text = raw_text.replace("\xa0", " ").strip().lower()

        # subscription?
        if is_channel_link(best) and ("subscribed to" in text or "subscribed channel" in text or text.startswith("subscribed")):
            add_unique(activity["subscribed"], best)
            continue

        # if it's a video link, decide liked vs watched
        if is_video_link(best):
            if is_liked_text(raw_text):
                add_unique(activity["liked"], best)
            else:
                add_unique(activity["watched"], best)
            continue

        # fallback: if link looks like channel, treat as subscribed
        if is_channel_link(best):
            add_unique(activity["subscribed"], best)

    # summary print
    print("\n✅ Parsing completed successfully!")
    print(f"• Watched: {len(activity['watched'])}")
    print(f"• Liked: {len(activity['liked'])}")
    print(f"• Subscribed: {len(activity['subscribed'])}")

    return activity


# --- small test harness you can run locally ---
def main():
    file_path = "data/MyActivity.html"  # update as needed
    activity = parse_takeout_html(file_path)
    # If you want, inspect lists:
    # print(activity['liked'][:10])

if __name__ == "__main__":
    main()

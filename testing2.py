import datetime
import pytz
from tzlocal import get_localzone  # auto-detects user's local timezone

def get_next_youtube_quota_reset():
    """
    Returns (reset_time_user_tz, time_left_timedelta)
    - reset_time_user_tz: a timezone-aware datetime in user's timezone
    - time_left_timedelta: time remaining until reset
    """
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


def main():
    reset_time, time_left = get_next_youtube_quota_reset()
    print("Next Quota Reset:", reset_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("Time Left:", format_time_left(time_left))


if __name__ == "__main__":
    main()

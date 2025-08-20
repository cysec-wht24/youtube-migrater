import argparse
from youtube_migrator import migration

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Migrater - migrate subscriptions and likes from Google Takeout"
    )
    parser.add_argument(
        "--takeout", "-t", default="data/MyActivity.html",
        help="Path to Google Takeout MyActivity.html file"
    )
    parser.add_argument(
        "--credentials", "-c", default="data/client_secret.json",
        help="Path to YouTube API client_secret.json"
    )
    parser.add_argument(
        "--max-subs", "-m", type=int, default=50,
        help="Maximum subscriptions per run"
    )

    args = parser.parse_args()

    # override defaults in migration
    migration.TAKEOUT_FILE = args.takeout
    migration.CREDENTIALS_FILE = args.credentials
    migration.MAX_SUBSCRIPTIONS_PER_RUN = args.max_subs

    migration.main()

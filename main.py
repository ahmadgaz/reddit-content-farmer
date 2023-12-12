import os
import random
from dotenv import load_dotenv
from redditcontentfarmer import RedditContentFarmer

load_dotenv()

subreddits = [
    "AmItheAsshole",
    "TIFU",
    "TrueOffMyChest",
    "cheating_stories",
    "pettyrevenge",
    "confession",
    "socialskills",
]
narrators = ["snoop", "mrbeast", "gwyneth", "male", "female", "narrator"]

rcf = RedditContentFarmer(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    verbose=True,
    track_used_posts=True,
)

rcf.get_posts(subreddit=random.choice(subreddits), word_limit=600, span="week")

rcf.create_video(
    pvleopard_access_key=os.getenv("PVLEOPARD_ACCESS_KEY"),
    narrator=random.choice(narrators),
)

rcf.upload_to_instagram(
    username=os.getenv("INSTAGRAM_USERNAME"),
    password=os.getenv("INSTAGRAM_PASSWORD"),
    input_path="output/output.mp4",
    output_path="output",
    caption=f"""
{rcf.post_title}
#redditfeeds #askreddit #reddit #redditstories #redditreadings #redditmemes #dating #datingadvice #memes #trending #funnymemes #nsfw #reels
""",
)

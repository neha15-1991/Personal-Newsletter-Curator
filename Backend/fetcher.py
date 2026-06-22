import os
import feedparser
import praw
import requests
from dotenv import load_dotenv


# Build the path of the .env file.
# fetcher.py is inside Backend, while .env is in the main folder.
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")

# Load secret values from the .env file.
load_dotenv(ENV_FILE_PATH)


def fetch_rss_stories(feed_url: str) -> list[dict]:
    """
    Fetches up to 10 stories from one RSS feed.
    """

    stories = []

    # Download and parse the RSS or Atom feed.
    feed = feedparser.parse(feed_url)

    # Stop with a clear error when the feed cannot be read
    # and no entries were returned.
    if feed.bozo and not feed.entries:
        raise ValueError("The RSS feed could not be read")

    # Use the feed title when available.
    # Otherwise, use the URL as the source name.
    source_name = feed.feed.get("title", feed_url)

    for entry in feed.entries[:10]:

        title = entry.get("title", "Untitled story")
        story_url = entry.get("link", "")
        content = entry.get("summary", entry.get("description", ""))
        published_at = entry.get("published", entry.get("updated", ""))

        # URL is required for opening and deduplicating stories.
        #if url not present then skip this loopitem from exceuting further and next loop item starts.
        #if url present then add in the stories.
        if not story_url:
            continue

        stories.append({
            "title": title,
            "url": story_url,
            "content": content,
            "source_type": "rss",
            "source_name": source_name,
            "published_at": published_at,

            # RSS usually does not provide engagement values.
            "engagement_score": 0,
            "comment_count": 0
        })

    return stories


def fetch_hn_stories(search_tag: str) -> list[dict]:
    """
    Fetches up to 10 Hacker News stories using the Algolia API.
    """

    stories = []

    api_url = "https://hn.algolia.com/api/v1/search"

    params = {
        "query": search_tag,
        "tags": "story",
        "hitsPerPage": 10
    }

    # Send the search request to Hacker News Algolia.
    response = requests.get(
        api_url,
        params=params,
        timeout=15
    )

    # Raise an error if the request was unsuccessful.
    response.raise_for_status()

    data = response.json()

    for item in data.get("hits", []):

        title = item.get("title")
        story_url = item.get("url")
        story_id = item.get("objectID")

        # Some HN posts do not have an external URL.
        # In that case, use the Hacker News discussion page.
        if not story_url and story_id:
            story_url = (
                "https://news.ycombinator.com/item?id="
                + story_id
            )

        if not title or not story_url:
            continue

        stories.append({
            "title": title,
            "url": story_url,

            # HN search results may not include article content,
            # so the title is used as basic text.
            "content": title,

            "source_type": "hn",
            "source_name": search_tag,
            "published_at": item.get("created_at", ""),
            "engagement_score": item.get("points") or 0,         #writing "or 0" outside get func provides value 0 if key is missing, nt missing but have value "None" or show "False values". 
            "comment_count": item.get("num_comments") or 0
        })

    return stories


def get_reddit_client() -> praw.Reddit:
    """
    Creates a read-only Reddit client.
    """

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    # Give a clear error when credentials are missing.
    if not client_id or not client_secret or not user_agent:
        raise ValueError(
            "Reddit credentials are missing from the .env file"
        )

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    # We only need to read public posts.
    reddit.read_only = True

    return reddit


def fetch_reddit_stories(subreddit_name: str) -> list[dict]:
    """
    Fetches up to 10 hot posts from one subreddit.
    """

    # Create an empty list to store fetched Reddit posts.
    stories = []

    # Create the Reddit API client.
    reddit = get_reddit_client()

    # Fetch up to 10 hot posts from the selected subreddit.
    for post in reddit.subreddit(subreddit_name).hot(limit=10):

        # Skip pinned posts created by subreddit moderators.
        if post.stickied:
            continue

        # Add the Reddit post to our stories list.
        stories.append({
            
            "title": post.title,

            # permalink contains only the path, so add Reddit's domain.
            "url": "https://www.reddit.com" + post.permalink,

            # Use the post body when available.
            # For link posts with no body, use the title.
            "content": post.selftext.strip() or post.title,

            "source_type": "reddit",
            "source_name": subreddit_name,

            # Reddit provides the date as a Unix timestamp.
            "published_at": str(post.created_utc),

            # Reddit upvotes minus downvotes.
            "engagement_score": post.score or 0,

            # Number of comments on the post.
            "comment_count": post.num_comments or 0
        })

    return stories
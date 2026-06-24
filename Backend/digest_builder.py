import json
from sqlalchemy.orm import Session

from models import Digest, Interest, Story, User
from ranker import get_ranked_stories
from summariser import summarise_story


def create_fallback_summary(story: Story) -> dict:
    """
    Creates a simple fallback summary when the AI summariser fails.
    This keeps the digest pipeline working even if Gemini/API fails.
    """

    content = story.content or ""
    title = story.title or "Untitled story"

    short_content = content.strip()

    if len(short_content) > 250:
        short_content = short_content[:250] + "..."

    if not short_content:
        short_content = "This story is relevant to the user's selected interests and saved sources."

    return {
        "summary": f"{title}. {short_content}",
        "why_it_matters": "This story may be useful because it matches the user's saved interests and selected news sources."
    }


def build_digest_for_user(user: User, db: Session, top_k: int = 5) -> dict:
    """
    Builds and saves one personalised digest for a user.

    Steps:
    1. Read the user's topic tags.
    2. Get the most relevant stories.
    3. Summarise each story using AI.
    4. Generate 'why this matters to you'.
    5. Save the completed digest in SQLite.

    Extra safety:
    - If Chroma ranking gives no results, use recent stories from SQLite.
    - If AI summarisation fails, create a fallback summary.
    """

    # Get all structured topic tags belonging to the user.
    user_interests = db.query(Interest).filter(
        Interest.user_id == user.id
    ).all()

    # Extract only the topic names.
    topic_names = [interest.topic for interest in user_interests]

    # The user must have at least free-text interests or one structured topic before building a digest.
    if not user.interest_text and not topic_names:
        raise ValueError("Please add your interests before building a digest")

    # Try to get ranked stories from ChromaDB.
    ranked_stories = get_ranked_stories(
        user_id=user.id,
        top_k=top_k
    )

    # Fallback: if ChromaDB has no ranked stories, use recent stories from SQLite.
    if not ranked_stories:
        recent_stories = (
            db.query(Story)
            .order_by(Story.id.desc())
            .limit(top_k)
            .all()
        )

        ranked_stories = []

        for story in recent_stories:
            ranked_stories.append({
                "story_id": story.id,
                "similarity_score": 0.0
            })

    if not ranked_stories:
        raise ValueError("No stories are available for digest creation")

    # Stores successfully processed digest cards.
    digest_items = []

    # Stores stories that could not be processed.
    failed_stories = []

    for ranked_story in ranked_stories:

        # Load the complete story from SQLite using the story ID.
        story = db.query(Story).filter(
            Story.id == ranked_story["story_id"]
        ).first()

        # Skip the result if the story no longer exists in SQLite.
        if story is None:
            failed_stories.append({
                "story_id": ranked_story["story_id"],
                "error": "Story not found in SQLite"
            })
            continue

        try:
            # Try AI summarisation first.
            generated_result = summarise_story(
                title=story.title,
                content=story.content,
                user_interest_text=user.interest_text,
                topics=topic_names
            )

        except Exception as error:
            # If AI summarisation fails, do not stop the pipeline.
            # Use fallback summary instead.
            failed_stories.append({
                "story_id": story.id,
                "title": story.title,
                "error": str(error),
                "fallback_used": True
            })

            generated_result = create_fallback_summary(story)

        # Create one complete digest story card.
        digest_items.append({
            "story_id": story.id,
            "title": story.title,
            "url": story.url,
            "source_type": story.source_type,
            "source_name": story.source_name,
            "published_at": story.published_at,
            "engagement_score": story.engagement_score,
            "comment_count": story.comment_count,
            "similarity_score": ranked_story.get("similarity_score", 0.0),
            "summary": generated_result.get("summary", "Summary not available."),
            "why_it_matters": generated_result.get(
                "why_it_matters",
                "This story is relevant to the user's saved interests."
            )
        })

    # If still no digest items, then there are really no usable stories.
    if not digest_items:
        raise ValueError("The digest could not be created because no usable stories were found")

    # Convert the Python list into a JSON string because digest_content is a Text database column.
    digest_json = json.dumps(
        digest_items,
        ensure_ascii=False
    )

    # Create one Digest database row for this user.
    new_digest = Digest(
        user_id=user.id,
        digest_content=digest_json
    )

    db.add(new_digest)

    try:
        # Save the digest permanently in SQLite.
        db.commit()

        # Reload generated values such as id and created_at.
        db.refresh(new_digest)

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Digest created successfully",
        "digest_id": new_digest.id,
        "created_at": new_digest.created_at,
        "story_count": len(digest_items),
        "stories": digest_items,
        "failed_stories": failed_stories
    }
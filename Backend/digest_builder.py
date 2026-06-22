import json
from sqlalchemy.orm import Session

from models import Digest, Interest, Story, User
from ranker import get_ranked_stories
from summariser import summarise_story


def build_digest_for_user(user: User, db: Session, top_k: int = 5) -> dict:
    """
    Builds and saves one personalised digest for a user.

    Steps:
    1. Read the user's topic tags.
    2. Get the most relevant stories.
    3. Summarise each story using Groq.
    4. Generate "why this matters to you".
    5. Save the completed digest in SQLite.
    """

    # Get all structured topic tags belonging to the user.
    user_interests = db.query(Interest).filter(Interest.user_id == user.id).all()

    # Extract only the topic names.
    topic_names = [interest.topic for interest in user_interests]

    # The user must have at least free-text interests or one structured topic before building a digest.
    if not user.interest_text and not topic_names:
        raise ValueError("Please add your interests before building a digest")

    # Get the stories that are most similar to the user's interest embedding.
    ranked_stories = get_ranked_stories(user_id=user.id, top_k=top_k)

    if not ranked_stories:
        raise ValueError(
            "No ranked stories are available"
        )

    # Stores successfully processed digest cards.
    digest_items = []

    # Stores stories that could not be processed.
    failed_stories = []

    for ranked_story in ranked_stories:

        # Load the complete story from SQLite using the story ID returned by ChromaDB.
        story = db.query(Story).filter(Story.id == ranked_story["story_id"]).first()

        # Skip the result if the story no longer exists in SQLite.
        if story is None:
            failed_stories.append({
                "story_id": ranked_story["story_id"],
                "error": "Story not found in SQLite"
            })

            continue

        try:
            # Ask Groq to create:
            # 1. A two-sentence summary
            # 2. A one-sentence personalised explanation
            generated_result = summarise_story(
                title=story.title,
                content=story.content,
                user_interest_text=user.interest_text,
                topics=topic_names
            )

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
                "similarity_score": ranked_story[
                    "similarity_score"
                ],
                "summary": generated_result["summary"],
                "why_it_matters": generated_result[
                    "why_it_matters"
                ]
            })

        except Exception as error:
            # One failed story should not stop the remaining stories.
            failed_stories.append({
                "story_id": story.id,
                "title": story.title,
                "error": str(error)
            })

    # Stop if Groq failed for every selected story.
    if not digest_items:
        raise ValueError(
            "The digest could not be created for any story"
        )

    # Convert the Python list into a JSON string
    # because digest_content is a Text database column.
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
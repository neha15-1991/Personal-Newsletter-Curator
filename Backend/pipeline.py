from sqlalchemy.orm import Session

from models import User
from digest_builder import build_digest_for_user


def run_curator_for_user(user: User, db: Session) -> dict:
    """
    Runs the complete curator pipeline for one user.

    This function is useful because both:
    1. Manual button
    2. APScheduler automatic job
    can call the same logic.
    """

    # Import inside the function to avoid circular import issues.
    from main import fetch_stories_now, embed_new_stories, embed_user_interests

    # Step 1: Fetch new stories from user's saved sources.
    fetch_result = fetch_stories_now(current_user=user, db=db)

    # Step 2: Create embeddings for newly fetched stories.
    story_embedding_result = embed_new_stories(db=db)

    # Step 3: Create/update the user's interest embedding.
    interest_embedding_result = embed_user_interests(current_user=user, db=db)

    # Step 4: Build and save personalised digest.
    try:
        digest_result = build_digest_for_user(user=user, db=db, top_k=5)

    except ValueError as error:
        # This prevents the whole pipeline from failing when:
        # - all stories are duplicates
        # - no story matches ranking rules
        # - digest builder cannot select a story
        digest_result = {
            "story_count": 0,
            "message": str(error),
            "status": "no_digest_created"
        }

    return {
        "message": "Curator pipeline completed",
        "fetch_result": fetch_result,
        "story_embedding_result": story_embedding_result,
        "interest_embedding_result": interest_embedding_result,
        "digest_result": digest_result
    }
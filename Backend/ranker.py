from embedder import interest_collection, story_collection


def get_ranked_stories(user_id: int, top_k: int = 5) -> list[dict]:
    """
    Returns the stories most relevant to one user.

    Steps:
    1. Get the user's interest embedding.
    2. Compare it with story embeddings.
    3. Return the closest matching stories.
    """

    # Get the stored interest embedding for this user.
    user_result = interest_collection.get(ids=[str(user_id)], include=["embeddings"])

    # Stop if no interest embedding exists for the user.
    if not user_result["ids"]:
        raise ValueError("User interest embedding was not found")

    # Extract the first embedding because each user has only one current interest embedding.
    user_embedding = user_result["embeddings"][0]

    # Check how many story embeddings exist.
    story_count = story_collection.count()

    if story_count == 0:
        return []

    # Do not request more stories than ChromaDB contains.
    number_of_results = min(top_k, story_count)

    # Compare the user's embedding with story embeddings.
    results = story_collection.query(
        query_embeddings=[user_embedding],
        n_results=number_of_results,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    ranked_stories = []

    # Chroma returns nested lists because it supports multiple queries in one request.
    story_ids = results["ids"][0]
    story_metadatas = results["metadatas"][0]
    story_distances = results["distances"][0]

    for story_id, metadata, distance in zip(
        story_ids,
        story_metadatas,
        story_distances
    ):
        # With cosine distance:
        # smaller distance means a better match.
        #
        # Convert distance into a simple similarity score.
        # ChromaDB returns cosine distance.
# Smaller distance means better match.
        raw_similarity = 1 - distance

        # Convert raw similarity from -1 to 1 range
        # into a friendly 0 to 1 range for display.
        display_score = (raw_similarity + 1) / 2

        ranked_stories.append({
            "story_id": int(story_id),
            "title": metadata.get("title", ""),
            "url": metadata.get("url", ""),
            "source_type": metadata.get(
                "source_type",
                ""
            ),
            "source_name": metadata.get(
                "source_name",
                ""
            ),
            "similarity_score": round(
                display_score,
                4
            )
        })

    return ranked_stories
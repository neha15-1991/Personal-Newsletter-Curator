from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# The ChromaDB files will be stored in:
# capstone-project/chroma_db/
CHROMA_DB_PATH = (
    Path(__file__).resolve().parent.parent / "chroma_db1"
)


# Load the embedding model once when this file is imported.
#
# This model converts text into numerical vectors.
# We will use the same model for both:
# 1. Story embeddings
# 2. User-interest embeddings
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# PersistentClient saves ChromaDB data on the computer,
# so embeddings remain available after restarting the app.
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DB_PATH)
)


# This collection will store story embeddings.
#
# get_or_create_collection means:
# - get the collection if it already exists
# - otherwise create it
story_collection = chroma_client.get_or_create_collection(
    name="story_embeddings",
     metadata={"hnsw:space": "cosine"}
     )


def create_story_text(title: str, content: str | None) -> str:
    """
    Combines a story's title and content into one text.
    The combined text gives the embedding model
    more information about the story.
    """

    # Use an empty string when content is None.
    safe_content = content or ""

    return f"{title}. {safe_content}".strip()


def create_embedding(text: str) -> list[float]:
    """
    Converts text into a numerical embedding vector.
    """

    # encode() returns a NumPy array.
    embedding = embedding_model.encode(text)

    # ChromaDB accepts a normal Python list, so convert the NumPy array into a list.
    return embedding.tolist()


def store_story_embedding( story_id: int, title: str, content: str | None,
    source_type: str,
    source_name: str,
    url: str
) -> None:
    """
    Creates and stores one story embedding in ChromaDB.
    """

    # Combine the title and content before embedding.
    story_text = create_story_text(title=title, content=content)

    # Convert the story text into an embedding.
    story_embedding = create_embedding(story_text)

    # Store the embedding in ChromaDB.
    #
    # The SQLite story id is converted into a string
    # because ChromaDB document ids are strings.
    story_collection.upsert(
        ids=[str(story_id)],
        embeddings=[story_embedding],
        documents=[story_text],
        metadatas=[
            {
                "story_id": story_id,
                "title": title,
                "url": url,
                "source_type": source_type,
                "source_name": source_name
            }
        ]
    )





# This collection stores one interest embedding for each user.
interest_collection = chroma_client.get_or_create_collection(
    name="user_interest_embeddings",
     metadata={"hnsw:space": "cosine"}
)    
def create_user_interest_text(interest_text: str | None, topics: list[str]) -> str:
    """
    Combines the user's free-text interest description
    and structured topic tags into one text.

    Example:
    Interest text:
    "I care about Python and artificial intelligence."

    Topics:
    ["Python", "Artificial Intelligence"]

    Combined result:
    "I care about Python and artificial intelligence.
    Topics: Python, Artificial Intelligence"
    """

    # Use an empty string if the user has not written
    # a free-text interest description.
    safe_interest_text = interest_text or ""

    # Join all topic names into one comma-separated string.
    topic_text = ", ".join(topics)

    # Combine the free-text description and topic tags.
    combined_text = (
        f"{safe_interest_text}. Topics: {topic_text}"
    )

    # Remove unnecessary spaces from the final text.
    return combined_text.strip()


def store_user_interest_embedding(user_id: int, interest_text: str | None, topics: list[str]) -> None:
    """
    Creates and stores one interest embedding
    for the user in ChromaDB.

    If the user's embedding already exists,
    upsert() updates it.
    """

    # Combine free-text interests and topic tags.
    combined_interest_text = create_user_interest_text(interest_text=interest_text, topics=topics)

    # Convert the combined interest text
    # into a numerical embedding vector.
    interest_embedding = create_embedding(
        combined_interest_text
    )

    # Save or update the user's interest embedding.
    interest_collection.upsert(
        # ChromaDB ids must be strings.
        ids=[str(user_id)],

        # The vector representing the user's interests.
        embeddings=[interest_embedding],

        # The original text used to create the vector.
        documents=[combined_interest_text],

        # Extra information stored with the embedding.
        metadatas=[
            {
                "user_id": user_id
            }
        ]
    )
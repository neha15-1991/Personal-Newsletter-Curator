from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, UniqueConstraint
from database import engine, Base
from datetime import datetime, timezone

#User table
class User(Base):
    __tablename__="users"
    
    id:Mapped[int]=mapped_column(primary_key=True)
   
    name:Mapped[str]=mapped_column(String(50), nullable=False)
   
    email:Mapped[str]=mapped_column(String, nullable=False, unique=True)
   
    password: Mapped[str]=mapped_column(String, nullable=False)
   
    interest_text: Mapped[str | None]=mapped_column(Text, nullable=True)

# User interests table
class Interest(Base):

    __tablename__ = "interests"

    id :Mapped[int]= mapped_column(primary_key=True)

    topic:Mapped[str]= mapped_column(String(100), nullable=False)

    user_id :Mapped[int]=mapped_column(ForeignKey("users.id"), nullable=False)
    
    __table_args__=(UniqueConstraint("user_id", "topic", name="unique_user_topic"),)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Allowed values: rss, reddit, hn
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # RSS URL, subreddit name, or Hacker News search tag
    source_value: Mapped[str] = mapped_column(String(500), nullable=False)

    # Connects this source to the logged-in user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Prevents the same user from adding the same source twice
    __table_args__ = (UniqueConstraint(
            "user_id",
            "source_type",
            "source_value",
            name="unique_user_source"
        ),
    )


class Story(Base):
    """
    Stores articles fetched from RSS feeds, Reddit, and Hacker News.
    """
    __tablename__ = "stories"

    # Unique id for every story saved in the database.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Title of the article or post.
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Original link of the story. The user will open this link when clicking the story card. 
    #unique=True prevents the same article from being saved twice
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    # Short article description, summary text, or post content received from RSS, Reddit, or Hacker News.
    # Some sources may not provide content, so it can be empty.
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Identifies where the story came from. Expected values: "rss", "reddit", or "hn".
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Stores the specific source name.eg. RSS -> "TechCrunch", Reddit -> "python",  Hacker News -> "artificial intelligence"
    source_name: Mapped[str] = mapped_column(String(500), nullable=False)

    # Publication date received from the external source. optional
    published_at: Mapped[str | None] = mapped_column(String(100), nullable=True)


    # Stores engagement received from the source.
    # Reddit: post score ,  Hacker News: story points
    # RSS: 0 because RSS normally does not provide engagement.
    engagement_score: Mapped[int] = mapped_column(default=0, nullable=False)


    # Stores the number of comments received from the source.
    # Reddit and Hacker News may provide this value.
    comment_count: Mapped[int] = mapped_column(default=0, nullable=False)


    # Stores the date and time when our application fetched the story.
    # If no value is given, the current UTC time is saved automatically.
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    
    # Shows whether this story has already been converted
    # into an embedding and stored in ChromaDB.
    # False means embedding is still pending.
    embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


    # Prevents the same story URL from being saved more than once for the same user.
    __table_args__ = (UniqueConstraint(
            "url",
            name="unique_story_url"
        ),
    )


class Digest(Base):
    """
    Stores one personalised newsletter digest
    created for a user.
    """
    __tablename__ = "digests"

    # Unique ID for each digest.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Connects the digest to the user for whom it was generated.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Stores all digest story cards as JSON text.
    digest_content: Mapped[str] = mapped_column(Text, nullable=False )

    # Automatically stores when the digest was created.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)    


class Click(Base):
    """
    Stores which story a user clicked.

    This helps us understand what the user actually liked.
    Later, click history can improve recommendations.
    """

    __tablename__ = "clicks"

    # Unique ID for each click record.
    id: Mapped[int] = mapped_column(primary_key=True)

    # The user who clicked the story.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # The story that was clicked.
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)

    # Time when the click happened.
    clicked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

def create_tables():
    """
    Creates all database tables that are defined in models.py.
    If a table already exists, SQLAlchemy will not create it again.
    """
    Base.metadata.create_all(engine)    
           
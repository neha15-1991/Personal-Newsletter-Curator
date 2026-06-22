from pydantic import BaseModel, EmailStr, Field
from typing import Annotated, Literal

#user 
class UserCreate(BaseModel):
    
    name:Annotated[str, Field(min_length=2, max_length=50, description="Full name of the user")]
    
    # EmailStr checks whether the value has a valid email format
    email:Annotated[EmailStr, Field(description="Email address must be valid")]
    
     # Password must contain at least 6 characters
    password:Annotated[str, Field(min_length=6, description="password must be atleast 8 characters long")]

class UserLogin(BaseModel):
    
    email: Annotated[EmailStr, Field(description="Registered email")]
    
     # Password must contain at least 6 characters
    password:Annotated[str, Field(min_length=6,description="user password")]  


class InterestEditor(BaseModel):
    """
    Receives the user's free-text interest description
    and a list of structured topic tags.
    """
    # Detailed answer to: "What topics or areas do you care about?"
    interest_text: Annotated[str,  Field(min_length=3, max_length=500, description="Free-text description of the user's interests")]

    
    # Structured topics used later for embedding and story ranking.
    # Example: ["Python", "Artificial Intelligence", "Solar Energy"]
    topics: Annotated[list[str], Field(min_length=1, description="List of topics the user wants to follow")] 




class SourceCreate(BaseModel):
    """
    Receives one source selected by the user.

    Supported source types:
    - rss
    - reddit
    - hn
    """

    # Literal ensures the user can enter only one of these three supported source types.
    source_type: Literal["rss", "reddit", "hn"]

    # Stores: RSS feed URL, subreddit name, or Hacker News search tag.
    source_value: Annotated[str, Field(min_length=2, max_length=500, description="RSS URL, subreddit name, or Hacker News tag")]       
    
    # example:{"source_type": "rss", "source_value": "https://techcrunch.com/feed/"}
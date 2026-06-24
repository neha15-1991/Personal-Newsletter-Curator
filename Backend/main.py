from fastapi import FastAPI, HTTPException, Depends, status
from models import create_tables, User, Interest, Source, Story, Digest, Click
from dependencies import get_db
from sqlalchemy.orm import Session
from schema import UserCreate, UserLogin, InterestEditor, SourceCreate
from auth import hash_password, create_access_token, verify_password, verify_access_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import json
from scheduler import run_daily_curator_job
from pipeline import run_curator_for_user
from fetcher import fetch_rss_stories, fetch_hn_stories, fetch_reddit_stories
from embedder import create_embedding, create_story_text, create_user_interest_text, store_story_embedding, store_user_interest_embedding
from ranker import get_ranked_stories
from digest_builder import build_digest_for_user
from scheduler import start_scheduler, stop_scheduler, run_daily_curator_job

# creates the fastapi application.
app=FastAPI(title="Personal Newsletter Curator API") 

# This line below helps fastapi read the token from this header->"Authorization: Bearer <token>""
bearer_scheme = HTTPBearer()

#ccreate database tables
create_tables()  

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    """
    Identifies the currently logged-in user from the JWT token.
    Steps:
    1. Read the Bearer token.
    2. Decode and verify the token.
    3. Get the user's email from the token.
    4. Find and return that user from the database.
    """
    # HTTPBearer separates the word "Bearer" from the actual token.
    token = credentials.credentials
    
    # Verify the token and get the email stored in its "sub" field.
    user_email = verify_access_token(token)

    # Reject the request when the token is invalid or expired.
    if user_email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token"
        )

    # Find the user whose email was stored in the token.
    user = db.query(User).filter(User.email == user_email).first()

    # The token may be valid, but the user could have been deleted.
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found"
        )

    return user  # otherwise return user

#homepage endpoint
@app.get("/")
def home_page():
    return {"message": "Newsletter Curator API running"}

# create user account 
@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(input_user_data:UserCreate, db:Session=Depends(get_db)):
    """
    Registers a new user.

    Steps:
    1. Check whether the email already exists.
    2. Hash the password.
    3. Save the user in the database.
    """
    # Check if a user with this email already exists
    existing_user= db.query(User).filter(User.email==str(input_user_data.email)).first()
    #check if user already exists.
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    #hash plain password 
    hashed_password=hash_password(input_user_data.password)   

    #create a new user object
    new_user=User(name=input_user_data.name,
              email=str(input_user_data.email), password=hashed_password)
    
    #add user to database session
    db.add(new_user)

    #save user permanently in database.
    db.commit() 

    #refresh object to get generated id.
    db.refresh(new_user)

    return {
        "message":"user registered succesfully",
        "user":{
            "id":new_user.id,
            "name":new_user.name,
            "email":new_user.email
        }
    }


#user login part
@app.post("/login")
def login(input_login_data: UserLogin, db: Session = Depends(get_db)):

    """
    Logs in an existing user.
    Steps:
    1. Find user by email.
    2. Check password.
    3. Create JWT token.
    4. Return token to the user.
    """
    # Search user by email.
    user = db.query(User).filter(
        User.email == str(input_login_data.email)).first()

    # If user does not exist, stop login.
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password(unauthorised)"
        )

    # Check whether entered password matches stored hashed password.
    password_is_correct = verify_password(input_login_data.password, user.password)

    if not password_is_correct:
        raise HTTPException(status_code=401, detail="invalid email or password")
    
    #otherwise
    #create jwt token.

    access_token=create_access_token(data={"sub":user.email})
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


#returns the profile of current loged-in users.
@app.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    
    # FastAPI first runs get_current_user().
    # If the token is valid, current_user contains the logged-in user.
    """
    Returns the profile of the currently logged-in user.
    This endpoint cannot be used without a valid JWT token.
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }




@app.put("/interests")
def save_interests(
    input_data: InterestEditor,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save or update user interests.

    This endpoint is designed to be safe even if the user saves
    the same interests again.
    """

    # Save the free-text interest description for the logged-in user
    current_user.interest_text = input_data.interest_text

    # Clean topic tags:
    # 1. remove extra spaces
    # 2. convert to lowercase
    # 3. remove duplicate tags
    cleaned_topics = []

    for topic in input_data.topics:
        cleaned_topic = topic.strip().lower()

        if cleaned_topic and cleaned_topic not in cleaned_topics:
            cleaned_topics.append(cleaned_topic)

    # Delete old topic tags for this user
    db.query(Interest).filter(
        Interest.user_id == current_user.id
    ).delete()

    # Very important:
    # flush tells SQLAlchemy to apply the delete before adding same tags again
    db.flush()

    # Add the new cleaned topic tags
    for topic in cleaned_topics:
        new_interest = Interest(
            topic=topic,
            user_id=current_user.id
        )

        db.add(new_interest)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Interests saved successfully",
        "interest_text": current_user.interest_text,
        "topics": cleaned_topics
    }

    
@app.get("/interests")
def get_interests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the logged-in user's current free-text interest
    description and structured topic tags.
    """

    # Fetch only the topics belonging to the logged-in user.
    user_interests = db.query(Interest).filter(
        Interest.user_id == current_user.id
    ).all()

    return {
        "interest_text": current_user.interest_text,
        "topics": [
            {
                "id": interest.id,
                "topic": interest.topic
            }
            for interest in user_interests    # using list comprehension.
        ]
    }    



@app.delete("/interests/{interest_id}")
def delete_interest(interest_id: int,  current_user: User = Depends(get_current_user),   db: Session = Depends(get_db)):
    """
    Deletes one topic tag belonging to the logged-in user.
    """

    # Search using both the topic id and the current user's id.
    # This prevents one user from deleting another user's topic.
    interest = db.query(Interest).filter(Interest.id == interest_id, Interest.user_id == current_user.id).first()

    if interest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest topic not found"
        )

    # Save the topic name before deletion
    # so it can be returned in the response.
    deleted_topic = interest.topic

    try:
        # Remove the selected topic.
        db.delete(interest)

        # Save the deletion permanently.
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete interest topic"
        )

    return {
        "message": "Interest topic deleted successfully",
        "deleted_topic": deleted_topic
    }


#-----------------------------------------------------------------SOURCE MANAGER ENDPOINTS----------------------------------------------------------
@app.post("/sources")
def add_source(input_source_data: SourceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Adds one source for the logged-in user.

    Source types:
    - rss
    - reddit
    - hn
    """

    cleaned_source_value = input_source_data.source_value.strip()

    # Check if this source already exists for this user.
    existing_source = db.query(Source).filter(
        Source.user_id == current_user.id,
        Source.source_type == input_source_data.source_type,
        Source.source_value == cleaned_source_value
    ).first()

    if existing_source:
        raise HTTPException(
            status_code=409,
            detail="This source already exists"
        )

    # Create a new source row.
    new_source = Source(
        source_type=input_source_data.source_type,
        source_value=cleaned_source_value,
        user_id=current_user.id
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return {
        "message": "Source added successfully",
        "source": {
            "id": new_source.id,
            "source_type": new_source.source_type,
            "source_value": new_source.source_value
        }
    }


@app.get("/sources")
def get_sources(current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
    """
    Returns all sources added by the logged-in user.
    """

    sources = db.query(Source).filter(Source.user_id == current_user.id).all()

    return {
        "sources": [
            {
                "id": source.id,
                "source_type": source.source_type,
                "source_value": source.source_value
                
            }
            for source in sources
        ]
    }


@app.delete("/sources/{source_id}")
def delete_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes one source belonging to the logged-in user.
    """

    source = db.query(Source).filter(
        Source.id == source_id,
        Source.user_id == current_user.id
    ).first()

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found"
        )

    deleted_source = source.source_value

    db.delete(source)
    db.commit()

    return {
        "message": "Source deleted successfully",
        "deleted_source": deleted_source
    }


#-------------------------------------------------------STORIES MANAGING ENDPOINTS----------------------------------------------------------------
@app.post("/fetch-now")
def fetch_stories_now(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Manually fetches stories from all sources saved
    by the currently logged-in user.

    Steps:
    1. Get the user's saved sources.
    2. Fetch stories from RSS, Hacker News, and Reddit.
    3. Check whether each story URL already exists.
    4. Save only newly ingested stories.
    """
    # Get all RSS, Reddit, and Hacker News sources belonging to the logged-in user.
    user_sources = db.query(Source).filter(Source.user_id == current_user.id).all()

    # Fetching cannot begin if the user has no sources.
    if not user_sources:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please add at least one source first")

    # Counts every story returned by external sources.
    total_fetched = 0

    # Counts only new stories saved in SQLite.
    total_saved = 0

    # Counts fetched stories whose URLs already exist.
    duplicates_skipped = 0

    # Stores errors from individual sources.
    # One failed source should not stop the other sources.
    failed_sources = []

    for source in user_sources:

        try:
            # Call the correct fetch function based on the saved source type.
            if source.source_type == "rss":
                fetched_stories = fetch_rss_stories(source.source_value)

            elif source.source_type == "hn":
                fetched_stories = fetch_hn_stories(source.source_value)

            elif source.source_type == "reddit":
                fetched_stories = fetch_reddit_stories(source.source_value)

            else:
                failed_sources.append({
                    "source_type": source.source_type,
                    "source_value": source.source_value,
                    "error": "Unsupported source type"
                })

                continue

            total_fetched += len(fetched_stories)

            for story_data in fetched_stories:

                # Check whether this URL is already saved.
                # Stories are stored globally, so user_id is not included in this query.
                existing_story = db.query(Story).filter(Story.url == story_data["url"]).first()

                # Skip the story when the URL already exists.
                if existing_story:
                    duplicates_skipped += 1
                    continue

                # Create a Story database object
                # for a newly ingested story.
                new_story = Story(
                    title=story_data["title"],
                    url=story_data["url"],
                    content=story_data["content"],
                    source_type=story_data["source_type"],
                    source_name=story_data["source_name"],
                    published_at=story_data["published_at"],
                    engagement_score=story_data["engagement_score"],
                    comment_count=story_data["comment_count"],

                    # False means this story has not yet been embedded and stored in ChromaDB.
                    embedded=False
                )

                db.add(new_story)
                total_saved += 1

        except Exception as error:
            # Record the source error and continue fetching stories from the remaining sources.
            failed_sources.append({
                "source_type": source.source_type,
                "source_value": source.source_value,
                "error": str(error)
            })

    try:
        # Save all newly ingested stories permanently.
        db.commit()

    except Exception as error:
        # Undo unfinished database changes if saving fails.
        db.rollback()

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save stories: {str(error)}")

    return {
        "message": "Story fetching completed",
        "total_fetched": total_fetched,
        "total_saved": total_saved,
        "duplicates_skipped": duplicates_skipped,
        "failed_sources": failed_sources
    }


@app.get("/stories")
def get_saved_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns all stories currently stored in SQLite.

    This endpoint is mainly used to test the Day 3
    fetching and storage workflow.
    """

    # Get the latest saved stories first.
    stories = db.query(Story).order_by(Story.id.desc()).all()

    return {
        "count": len(stories),
        "stories": [
            {
                "id": story.id,
                "title": story.title,
                "url": story.url,
                "content": story.content,
                "source_type": story.source_type,
                "source_name": story.source_name,
                "published_at": story.published_at,
                "engagement_score": story.engagement_score,
                "comment_count": story.comment_count,
                "embedded": story.embedded
            }
            for story in stories
        ]
    }

#-------------------------------------------EMBED_STORIES ENDPOINT---------------------------------------------------
@app.post("/embed-stories")
def embed_new_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Creates embeddings only for stories that have not
    yet been stored in ChromaDB.
    A story needs embedding when:
    embedded == False
    """
    
    # Fetch only newly ingested stories.
    new_stories = db.query(Story).filter(Story.embedded == False).all()

    # Return early when every story is already embedded.
    if not new_stories:
        return {
            "message": "No new stories need embeddings",
            "embedded_count": 0,
            "failed_stories": []
        }

    embedded_count = 0
    failed_stories = []

    for story in new_stories:
        try:
            # Create the story embedding and store it in ChromaDB.
            store_story_embedding(
                story_id=story.id,
                title=story.title,
                content=story.content,
                source_type=story.source_type,
                source_name=story.source_name,
                url=story.url
            )

            # Mark the story as embedded in SQLite.
            story.embedded = True

            embedded_count += 1

        except Exception as error:
            # One failed story should not stop the remaining stories.
            failed_stories.append({
                "story_id": story.id,
                "title": story.title,
                "error": str(error)
            })

    try:
        # Save all embedded=True changes in SQLite.
        db.commit()

    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not update story records: {str(error)}")

    return {
        "message": "Story embedding completed",
        "embedded_count": embedded_count,
        "failed_stories": failed_stories
    }

#----------------------------------------------EMBED INTERESTS----------------------------------------------------
@app.post("/embed-interests")
def embed_user_interests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Creates or updates the logged-in user's
    interest embedding in ChromaDB.

    The embedding is created from:
    1. Free-text interest description
    2. Structured topic tags
    """
    

    # Get all topic tags belonging to the current user.
    user_interests = db.query(Interest).filter(Interest.user_id == current_user.id).all()

    # Extract only the topic names.
    topic_names = [interest.topic for interest in user_interests]

    # The user must save interests before creating an interest embedding.
    if not current_user.interest_text and not topic_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add your interests first"
        )

    try:
        # Create or update the user's interest embedding.
        store_user_interest_embedding(
            user_id=current_user.id,
            interest_text=current_user.interest_text,
            topics=topic_names
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not embed user interests: {str(error)}"
        )

    return {
        "message": "User interest embedding created successfully",
        "user_id": current_user.id,
        "interest_text": current_user.interest_text,
        "topics": topic_names
    }


#--------------------------------GET RECOMMENDED STORIES ENDPOINT-------------------------------------------------
@app.get("/recommended-stories")
def get_recommended_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the top five stories that best match
    the logged-in user's interests.
    Steps:
    1. Use the user's interest embedding.
    2. Compare it with story embeddings in ChromaDB.
    3. Get the most relevant story IDs.
    4. Load complete story information from SQLite.
    """
    
    try:
        # Get up to five stories whose embeddings are closest to the current user's interest embedding.
        ranked_results = get_ranked_stories( user_id=current_user.id, top_k=5)

    except ValueError as error:
        # This may happen when the user-interest embedding has not been created yet.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not rank stories: {str(error)}")

    recommendations = []

    for ranked_story in ranked_results:

        # Find the complete story in SQLite using the ID returned by ChromaDB.
        story = db.query(Story).filter(Story.id == ranked_story["story_id"]).first()

        # Skip the result if its SQLite story no longer exists.
        if story is None:
            continue

        recommendations.append({
            "id": story.id,
            "title": story.title,
            "url": story.url,
            "content": story.content,
            "source_type": story.source_type,
            "source_name": story.source_name,
            "published_at": story.published_at,
            "engagement_score": story.engagement_score,
            "comment_count": story.comment_count,
            "similarity_score": ranked_story[
                "similarity_score"
            ]
        })

    return {
        "count": len(recommendations),
        "recommendations": recommendations
    }



#--------------------------------------ENDPOINT FOR DIGEST_BUILDER--------------------------------------------------
@app.post("/build-digest", status_code=status.HTTP_201_CREATED)
def build_digest(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Builds and saves a personalised newsletter digest
    for the currently logged-in user.

    This endpoint connects:
    1. Ranked stories
    2. Groq summaries
    3. Why this matters explanation
    4. Digest saving in SQLite
    """
    from digest_builder import build_digest_for_user

    try:
        return build_digest_for_user(
            user=current_user,
            db=db,
            top_k=5
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not build digest: {str(error)}"
        )
    



@app.get("/digests")
def get_my_digests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns all saved digests for the logged-in user.
    """

    # Get this user's digests, newest first.
    user_digests = db.query(Digest).filter(Digest.user_id == current_user.id).order_by(
        Digest.id.desc()).all()

    return {
        "count": len(user_digests),
        "digests": [
            {
                "id": digest.id,
                "created_at": digest.created_at,

                # digest_content is stored as JSON text, so we convert it back into a Python list.
                "stories": json.loads(digest.digest_content)
            }
            for digest in user_digests
        ]
    }    



#------------------------------------------Click endpoint------------------------------------------------------------

@app.post("/clicks/{story_id}")
def record_click(story_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Records that the logged-in user clicked a story.
    """

    # First check whether this story exists.
    story = db.query(Story).filter(Story.id == story_id).first()

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )

    # Create a new click row.
    new_click = Click(
        user_id=current_user.id,
        story_id=story_id
    )

    db.add(new_click)
    db.commit()
    db.refresh(new_click)

    return {
        "message": "Click recorded successfully",
        "click_id": new_click.id,
        "story_id": story_id,
        "clicked_at": new_click.clicked_at
    }

@app.get("/clicks")
def get_my_clicks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns all stories clicked by the logged-in user.
    """

    clicks = db.query(Click).filter(Click.user_id == current_user.id).order_by(Click.id.desc()).all()

    result = []

    for click in clicks:
        story = db.query(Story).filter(Story.id == click.story_id).first()

        result.append({
            "click_id": click.id,
            "story_id": click.story_id,
            "clicked_at": click.clicked_at,
            "story_title": story.title if story else "Story deleted",
            "story_url": story.url if story else None
        })

    return {
        "count": len(result),
        "clicks": result
    }

#-----------------------------------------RUN CURATOR PIPELINE-------------------------------------------------------
@app.post("/run-curator")
def run_curator(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Runs the full curator pipeline for the logged-in user.

    Flow:
    1. Fetch stories
    2. Embed new stories
    3. Embed user interests
    4. Build digest
    """
    from pipeline import run_curator_for_user
    try:
        return run_curator_for_user(
            user=current_user,
            db=db
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not run curator pipeline: {str(error)}"
        )
    


@app.on_event("startup")
def startup_event():
    create_tables()
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()


@app.post("/run-scheduler-now")
def run_scheduler_now():
    """
    Manually runs the same job that APScheduler
    would run automatically every day.
    """
    return run_daily_curator_job()
    

    
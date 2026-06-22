from database import Session

def get_db():
    db = Session()      #open the databse session for each request.
    try:
        yield db       # Give the session to the route
                        # Example:
                        # db = Depends(get_db)
    finally:            #always remembers to close the database session always even if there is any exception/error.
        db.close()
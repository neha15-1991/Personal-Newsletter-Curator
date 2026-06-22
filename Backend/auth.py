import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError


#secret key is used to sign the jwt token.
SECRET_KEY="my_super_secret_key"

#algorithm to create the token.
ALGORITHM="HS256"

#token will expire in 60 mins.

ACCESS_TOKEN_EXPIRE_TIME=60


#convert the user password into hash password before storing into database.
#utf-8 is encoding method used to convert string into bytes so that machine can store and transmit data for the app.
def hash_password(password:str)->str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

#verify password at the time of login with the hash password(stored password).
def verify_password(plain_password:str, hashed_password:str)->bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data:dict)->str:
    """data is the user information.
    """
    token_data=data.copy()  #copy data to avoid changing original data.
    
    expire_time=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
   
    token_data.update({"exp":expire_time})  #add expire time inside token data

    token=jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token
    


def verify_access_token(token: str) -> str | None:
    """
    Verifies the JWT token and returns the user's email.
    Returns None if the token is invalid or expired.
    """

    try:
        # Decode the token using the same key and algorithm
        # that were used while creating it.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Get the user's email stored in the "sub" field.
        user_email = payload.get("sub")

        # Reject the token if "sub" is missing.
        if user_email is None:
            return None
        return user_email

    except JWTError:
        # This runs when the token is invalid, changed, or expired.
        return None
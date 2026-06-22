from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///my_project.db"

engine = create_engine(DATABASE_URL, echo=False)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
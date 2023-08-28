from sqlalchemy import ARRAY, Boolean, Column, Integer, String

from .database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    secret_key = Column(String, unique=True, index=True)
    target_url = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    clicks = Column(Integer, default=0)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    fullname = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, unique=True, index=True)
    scopes = Column(ARRAY(String))
    disabled = Column(Boolean, default=False)
    urls = Column(ARRAY(String))

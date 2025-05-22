from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Message(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

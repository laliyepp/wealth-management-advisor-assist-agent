from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    message_type = Column(String(10), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    meta_data = Column(Text)  # JSON string for additional data
    timestamp = Column(DateTime, default=datetime.utcnow)
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# MySQL database URL
DATABASE_URL = "mysql+pymysql://root:root@127.0.0.1:3306/gpt_app"

engine = create_engine(DATABASE_URL, echo=True) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)

    created_at = Column(DateTime, default=func.now())  # Created timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updated timestamp
    deleted_at = Column(DateTime, nullable=True)  # Soft delete timestamp

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    session_title = Column(String(2000))

    created_at = Column(DateTime, default=func.now())  # Created timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updated timestamp
    deleted_at = Column(DateTime, nullable=True)  # Soft delete timestamp

    user = relationship("User", back_populates="sessions")
    chats = relationship("Chat", back_populates="session", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    message = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)  # Make it nullable
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))

    created_at = Column(DateTime, default=func.now())  # Created timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updated timestamp
    deleted_at = Column(DateTime, nullable=True)  # Soft delete timestamp

    user = relationship("User", back_populates="chats")
    session = relationship("Session", back_populates="chats")
# Create the database tables
Base.metadata.create_all(bind=engine)

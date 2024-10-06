from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session ,joinedload
from typing import List, Optional  # Import Optional
from models import SessionLocal, User, Session as DBSession, Chat, Base  # Renamed Session to DBSession to avoid naming conflict
from pydantic import BaseModel
from auth_utils import verify_password , get_password_hash
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

client = OpenAI(api_key="")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular development server origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    password_hash: str
    
# Pydantic Models
class LoginUser(BaseModel):
    email: str
    password_hash: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class SessionCreate(BaseModel):
    user_id: int
    session_title: str

class SessionResponse(BaseModel):  # Add SessionResponse
    id: int
    user_id: int
    session_title: str

    class Config:
        orm_mode = True

class ChatCreate(BaseModel):
    user_id: int
    message: str
    session_id :int

class ChatResponse(BaseModel):
    id: int
    user_id: int
    message: str
    answer: str
    session_id:int

    class Config:
        orm_mode = True
        
class ChatModel(BaseModel):
    id: int
    message: str
    user_id:int
    answer: Optional[str]  # This can be None if there's no answer

class SessionModel(BaseModel):
    id: int
    session_title: str
    user_id:int
    chats: List[ChatModel]  # List of ChatModel objects

class UserModel(BaseModel):
    id: int
    username: str
    email: str
    sessions: List[SessionModel]  # List of SessionModel objects

class DeleteResponse(BaseModel):
    message: str

# Create User
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password_hash)
    db_user = User(username=user.username, email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login User
@app.post("/login/", response_model=UserModel)
def create_user(login_user: LoginUser, db: Session = Depends(get_db)):
    user = db.query(User).options(
        joinedload(User.sessions).joinedload(DBSession.chats)
    ).filter(User.email == login_user.email).first()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email"
            )
    
    if not verify_password(login_user.password_hash, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
   
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "sessions": [
            {
                "id": session.id,
                "user_id": user.id,
                "session_title": session.session_title,
                "chats": [
                    {
                        "id": chat.id,
                        "user_id": user.id,
                        "message": chat.message,
                        "answer": chat.answer,
                    } for chat in session.chats
                ]
            } for session in user.sessions
        ]
    }

# Read Users
@app.get("/users/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# Create Session
@app.post("/sessions/", response_model=SessionResponse)  # Change response_model
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_session = DBSession(user_id=session.user_id, session_title=session.session_title)  # Use DBSession
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# Create Chat
@app.post("/chats/", response_model=ChatResponse)
def create_chat(chat: ChatCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == chat.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    

    db_chat = Chat(user_id=chat.user_id, message=chat.message, answer='To add icons that indicate whether a message is from the user or from GPT, you can use icon libraries like FontAwesome or Material Icons. For this example, I’ll use FontAwesome icons, but you can easily swap in another icon set if you prefer.To add icons that indicate whether a message is from the user or from GPT, you can use icon libraries like FontAwesome or Material Icons. For this example, I’ll use FontAwesome icons, but you can easily swap in another icon set if you prefer.To add icons that indicate whether a message is from the user or from GPT, you can use icon libraries like FontAwesome or Material Icons. For this example, I’ll use FontAwesome icons, but you can easily swap in another icon set if you prefer.To add icons that indicate whether a message is from the user or from GPT, you can use icon libraries like FontAwesome or Material Icons. For this example, I’ll use FontAwesome icons, but you can easily swap in another icon set if you prefer.',session_id=chat.session_id)  # Default to None
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

# Read Chats by User ID
@app.get("/users/{user_id}/chats", response_model=UserModel)
def read_chats_by_user(user_id: int, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).options(
        joinedload(User.sessions).joinedload(DBSession.chats)
    ).filter(User.id == user_id).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sorted_sessions = sorted(
        user.sessions,
        key=lambda session: session.updated_at,
        reverse=True
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "sessions": [
            {
                "id": session.id,
                "user_id": user.id,
                "session_title": session.session_title,
                "chats": sorted(
                    session.chats,
                    key=lambda chat: chat.updated_at,
                    reverse=False
                )
            } for session in sorted_sessions
        ]
    }

@app.delete("/session/{session_id}", response_model=DeleteResponse)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated chats
    for chat in session.chats:
        db.delete(chat)

    # Now delete the session itself
    db.delete(session)
    db.commit()

    return DeleteResponse(message="Session and associated chats deleted successfully")



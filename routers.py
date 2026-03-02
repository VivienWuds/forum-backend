from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models import User, Topic, Post
from schemas import *
from auth import get_password_hash, verify_password, create_access_token, get_current_user, truncate_password

router = APIRouter()

# ---------- Аутентификация ----------
@router.post("/register", response_model=UserOut, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка длины пароля (в байтах)
    password_bytes = user.password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(400, "Password too long (max 72 bytes when encoded)")
    if len(user.password) < 3:
        raise HTTPException(400, "Password too short (min 3 characters)")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "Username already taken")
    
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Проверка длины пароля
    password_bytes = form_data.password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(400, "Password too long (max 72 bytes)")
    
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ---------- Темы ----------
@router.get("/topics", response_model=List[TopicOut])
def get_topics(db: Session = Depends(get_db)):
    topics = db.query(
        Topic, User.username, func.count(Post.id).label("message_count")
    ).join(
        User, Topic.author_id == User.id
    ).outerjoin(
        Post, Post.topic_id == Topic.id
    ).group_by(
        Topic.id
    ).order_by(
        Topic.created_at.desc()
    ).all()
    
    return [{
        "id": t.id,
        "title": t.title,
        "content": t.content,
        "author_id": t.author_id,
        "created_at": t.created_at,
        "username": username,
        "message_count": count
    } for t, username, count in topics]

@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(
    topic: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_topic = Topic(**topic.dict(), author_id=current_user.id)
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    return {
        "id": db_topic.id,
        "title": db_topic.title,
        "content": db_topic.content,
        "author_id": db_topic.author_id,
        "created_at": db_topic.created_at,
        "username": current_user.username,
        "message_count": 0
    }

@router.get("/topics/{topic_id}", response_model=TopicDetailOut)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(404, "Topic not found")
    
    author = db.query(User).filter(User.id == topic.author_id).first()
    
    posts = db.query(Post, User.username).join(
        User, Post.author_id == User.id
    ).filter(
        Post.topic_id == topic_id
    ).order_by(
        Post.created_at.asc()
    ).all()
    
    return {
        "id": topic.id,
        "title": topic.title,
        "content": topic.content,
        "username": author.username,
        "created_at": topic.created_at,
        "posts": [{
            "id": p.id,
            "content": p.content,
            "author_id": p.author_id,
            "username": username,
            "created_at": p.created_at
        } for p, username in posts]
    }

# ---------- Сообщения ----------
@router.post("/topics/{topic_id}/posts", response_model=PostOut, status_code=201)
def create_post(
    topic_id: int,
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not db.query(Topic).filter(Topic.id == topic_id).first():
        raise HTTPException(404, "Topic not found")
    
    db_post = Post(content=post.content, topic_id=topic_id, author_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return {
        "id": db_post.id,
        "content": db_post.content,
        "author_id": db_post.author_id,
        "username": current_user.username,
        "created_at": db_post.created_at
    }
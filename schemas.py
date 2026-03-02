from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

# Topic schemas
class TopicCreate(BaseModel):
    title: str
    content: str

class TopicOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    username: str
    created_at: datetime
    message_count: int = 0
    class Config:
        from_attributes = True

# Post schemas
class PostCreate(BaseModel):
    content: str

class PostOut(BaseModel):
    id: int
    content: str
    author_id: int
    username: str
    created_at: datetime
    class Config:
        from_attributes = True

class TopicDetailOut(BaseModel):
    id: int
    title: str
    content: str
    username: str
    created_at: datetime
    posts: List[PostOut]
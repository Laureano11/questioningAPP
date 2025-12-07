from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

# Esta clase define cómo es un usuario en Python Y cómo es la tabla en la BD
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str
    password: str  # Por ahora en texto plano (luego aprenderemos a encriptar)

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(default=None)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    #uploaded_by: int = Field(default=None, foreign_key="user.id")

class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    uploaded_at: datetime = Field(default=None)
    question_id: int = Field(default=None, foreign_key="question.id")
    #uploaded_by: int= Field(default=None, foreign_key="user.id")

from typing import Annotated
from pydantic import BaseModel, StringConstraints

SessionId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,100}$")]


class ChatRequest(BaseModel):
    session_id: SessionId
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]

class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    ai_response: str

class MessageItem(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageItem]

class SessionItem(BaseModel):
    session_id: str
    title: str
    created_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionItem]

class SessionRenameRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]

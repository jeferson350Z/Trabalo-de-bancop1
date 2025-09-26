from pydantic import BaseModel, Field
from datetime import datetime

class MessageIn(BaseModel):
    username: str = Field(..., max_length=50)
    content: str = Field(..., max_length=1000)

class MessageOut(MessageIn):
    id: str
    room: str
    created_at: datetime

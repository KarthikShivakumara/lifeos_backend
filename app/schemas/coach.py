from pydantic import BaseModel


class CoachMessage(BaseModel):
    message: str
    context: dict | None = None


class CoachReply(BaseModel):
    reply: str
    safety_note: str


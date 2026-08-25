from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message inquiry")
    conversation_id: str | None = Field(None, description="Optional active conversation ID")


class AssistantCitation(BaseModel):
    title: str = Field(..., description="Cited medical document title")
    source: str = Field(..., description="Issuing medical authority or organization")
    url: str = Field(..., description="Source guideline URL")
    relevance_score: float = Field(..., description="RAG vector similarity score")


class AssistantResponse(BaseModel):
    conversation_id: str = Field(..., description="Unique conversation thread identifier")
    answer: str = Field(..., description="Educational AI Assistant response text")
    citations: list[AssistantCitation] = Field(default=[], description="Cited medical references")
    context_used: list[str] = Field(default=[], description="User health data context items utilized")
    safety_category: str = Field(..., description="Safety classification of the query")
    disclaimer: str = Field(..., description="Mandatory non-diagnostic medical disclaimer")


class MessageItemSchema(BaseModel):
    id: str
    role: str
    content: str
    citations: list[AssistantCitation] = []
    safety_category: str | None = None
    created_at: str


class ConversationSummarySchema(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationDetailSchema(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[MessageItemSchema]

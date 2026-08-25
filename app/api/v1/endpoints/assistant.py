from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.assistant_service import assistant_service
from app.core.deps import get_current_user, get_db
from app.models.conversation import ConversationModel
from app.models.message import MessageModel
from app.models.user import User
from app.schemas.assistant import (
    AssistantCitation,
    AssistantRequest,
    AssistantResponse,
    ConversationDetailSchema,
    ConversationSummarySchema,
    MessageItemSchema,
)

router = APIRouter()


@router.post("/assistant/chat", response_model=AssistantResponse, summary="Send Message to AI Health Assistant")
def chat(
    payload: AssistantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantResponse:
    """Send an inquiry to the RAG-empowered AI Health Assistant with user-isolated health context."""
    return assistant_service.process_chat_message(
        user_id=current_user.id,
        message=payload.message,
        conversation_id=payload.conversation_id,
        db=db,
    )


@router.get("/assistant/conversations", response_model=list[ConversationSummarySchema], summary="List User Conversations")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationSummarySchema]:
    """Retrieve all conversations belonging to the authenticated user."""
    convs = (
        db.query(ConversationModel)
        .filter(ConversationModel.user_id == current_user.id)
        .order_by(ConversationModel.updated_at.desc())
        .all()
    )
    result: list[ConversationSummarySchema] = []
    for c in convs:
        result.append(
            ConversationSummarySchema(
                id=c.id,
                title=c.title,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
                message_count=len(c.messages),
            )
        )
    return result


@router.get(
    "/assistant/conversations/{conversation_id}",
    response_model=ConversationDetailSchema,
    summary="Get Conversation Messages",
)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetailSchema:
    """Get full message thread of a specific conversation (user isolation verified)."""
    conv = (
        db.query(ConversationModel)
        .filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )

    msg_items: list[MessageItemSchema] = []
    for m in conv.messages:
        citations: list[AssistantCitation] = []
        if m.citations_json:
            try:
                raw_c = json.loads(m.citations_json)
                citations = [AssistantCitation(**c) for c in raw_c]
            except Exception:
                pass
        msg_items.append(
            MessageItemSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                citations=citations,
                safety_category=m.safety_category,
                created_at=m.created_at.isoformat(),
            )
        )

    return ConversationDetailSchema(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        messages=msg_items,
    )


@router.delete(
    "/assistant/conversations/{conversation_id}",
    summary="Delete Conversation",
)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a specific conversation thread (user isolation verified)."""
    conv = (
        db.query(ConversationModel)
        .filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    db.delete(conv)
    db.commit()
    return {"status": "ok", "deleted_id": conversation_id}

from __future__ import annotations

import json
import logging, uuid
from typing import Any

from sqlalchemy.orm import Session

from app.ai.context_builder import context_builder
from app.ai.llm_client import llm_client
from app.ai.prompts import build_assistant_prompt
from app.ai.safety import EMERGENCY_DISCLAIMER, MANDATORY_SAFETY_DISCLAIMER, safety_classifier
from app.models.conversation import ConversationModel
from app.models.message import MessageModel
from app.rag.rag_service import rag_service
from app.schemas.assistant import AssistantCitation, AssistantResponse

logger = logging.getLogger("lifeos.assistant_service")


class AssistantService:
    _instance: AssistantService | None = None

    @classmethod
    def get_instance(cls) -> AssistantService:
        if cls._instance is None:
            cls._instance = AssistantService()
        return cls._instance

    def process_chat_message(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        db: Session | None = None,
    ) -> AssistantResponse:
        # 1. Conversation resolution
        active_conv: ConversationModel | None = None
        if db is not None:
            if conversation_id:
                active_conv = (
                    db.query(ConversationModel)
                    .filter(ConversationModel.id == conversation_id, ConversationModel.user_id == user_id)
                    .first()
                )

            if not active_conv:
                conv_title = message[:30] + ("..." if len(message) > 30 else "")
                active_conv = ConversationModel(
                    id=conversation_id or f"conv-{uuid.uuid4().hex[:10]}",
                    user_id=user_id,
                    title=conv_title,
                )
                db.add(active_conv)
                db.commit()
                db.refresh(active_conv)

        cid = active_conv.id if active_conv else (conversation_id or f"conv-{uuid.uuid4().hex[:10]}")

        # 2. Safety classification
        safety_cat = safety_classifier.classify_query(message)

        # 3. Retrieve user health context (user isolated)
        user_context = context_builder.build_user_context(user_id=user_id, db=db)

        # 4. Retrieve RAG medical knowledge
        rag_results = rag_service.retrieve_relevant_guidelines(
            query=message,
            context_summary=f"{user_context.top_priority_disease or ''} {user_context.overall_risk_level or ''}",
            top_k=3,
        )

        citations: list[AssistantCitation] = []
        chunks_text_list: list[str] = []
        context_used_labels: list[str] = []

        for res in rag_results:
            citations.append(
                AssistantCitation(
                    title=res.chunk.title,
                    source=res.chunk.source,
                    url=res.chunk.source_url,
                    relevance_score=round(res.similarity_score, 4),
                )
            )
            chunks_text_list.append(f"[{res.chunk.title}] ({res.chunk.source}): {res.chunk.text}")

        if user_context.has_assessment:
            context_used_labels.append("Latest LifeOS Assessment Results")
            if user_context.top_priority_disease:
                context_used_labels.append(f"Top Priority: {user_context.top_priority_disease}")
            if user_context.trend_summary:
                context_used_labels.append("Longitudinal Health Trend Data")

        chunks_str = "\n\n".join(chunks_text_list) if chunks_text_list else "No additional specific guidelines retrieved."

        # 5. Build prompt and call LLM
        prompt = build_assistant_prompt(
            user_query=message,
            user_context_str=user_context.formatted_context_str,
            retrieved_chunks_str=chunks_str,
            safety_category=safety_cat,
        )

        user_ctx_dict = {
            "top_priority_disease": user_context.top_priority_disease,
            "overall_risk_percentage": user_context.overall_risk_percentage,
            "disease_risks": user_context.disease_risks,
            "trend_summary": user_context.trend_summary,
        }

        raw_answer = llm_client.generate_response(
            prompt=prompt,
            user_query=message,
            safety_category=safety_cat,
            user_context_dict=user_ctx_dict,
            retrieved_chunks=rag_results,
        )

        # 6. Safety validation of response text
        validated_answer, _ = safety_classifier.validate_output(raw_answer, user_context.formatted_context_str)

        disclaimer = EMERGENCY_DISCLAIMER if safety_cat in ["emergency_question", "urgent_symptom_question"] else MANDATORY_SAFETY_DISCLAIMER

        # 7. Persist messages into DB
        if db is not None and active_conv:
            try:
                user_msg = MessageModel(
                    conversation_id=active_conv.id,
                    role="user",
                    content=message,
                    safety_category=safety_cat,
                )
                db.add(user_msg)

                citations_json = json.dumps([c.model_dump() for c in citations])
                assistant_msg = MessageModel(
                    conversation_id=active_conv.id,
                    role="assistant",
                    content=validated_answer,
                    citations_json=citations_json,
                    safety_category=safety_cat,
                )
                db.add(assistant_msg)
                db.commit()
            except Exception as err:
                logger.warning("Failed to persist conversation messages in DB: %s", err)
                db.rollback()

        return AssistantResponse(
            conversation_id=cid,
            answer=validated_answer,
            citations=citations,
            context_used=context_used_labels,
            safety_category=safety_cat,
            disclaimer=disclaimer,
        )


assistant_service = AssistantService.get_instance()

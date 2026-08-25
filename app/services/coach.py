def answer_health_query(message: str, context: dict | None = None) -> dict[str, str]:
    normalized = message.lower()
    if "risk" in normalized or "prediction" in normalized:
        reply = "I can help interpret risk trends and explain likely contributors from your latest assessment."
    elif "sleep" in normalized:
        reply = "A steady sleep schedule, reduced late caffeine, and a calm wind-down routine usually help the most."
    elif "diet" in normalized or "food" in normalized:
        reply = "A balanced plate with protein, fiber, and adequate hydration is a strong baseline for lifestyle improvement."
    else:
        reply = "I can summarize assessments, explain risk factors, and suggest practical lifestyle improvements."
    if context and context.get("overall_health_risk", 0) >= 65:
        reply += " Based on the current context, prioritizing recovery and routine check-ins would be especially useful."
    return {
        "reply": reply,
        "safety_note": "This assistant supports health decisions but does not diagnose or replace clinical care.",
    }


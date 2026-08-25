from app.ml.interfaces import CoachModel


class GeminiCoachAdapter:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ""

    def respond(self, message: str, context: dict | None = None) -> str:
        normalized = message.lower()
        if "sleep" in normalized:
            return "Focus on consistent sleep timing, a calmer wind-down, and less late caffeine."
        if "diet" in normalized or "food" in normalized:
            return "A balanced plate with fiber, protein, and hydration is a strong foundation."
        if context and context.get("overall_health_risk", 0) >= 65:
            return "The current risk context suggests prioritizing recovery, movement, and routine follow-up."
        return "I can explain risk patterns, assessment trends, and practical lifestyle improvements."


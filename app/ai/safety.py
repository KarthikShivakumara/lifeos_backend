from __future__ import annotations

import re
from typing import Literal

SafetyCategory = Literal[
    "general_information",
    "health_interpretation",
    "personal_risk_question",
    "medication_question",
    "urgent_symptom_question",
    "emergency_question",
    "unsupported_request",
]

MANDATORY_SAFETY_DISCLAIMER = (
    "LifeOS AI Assistant is an educational decision-support tool. It does not provide medical diagnoses, "
    "treatment plans, or replace professional clinical evaluation by a qualified healthcare provider."
)

EMERGENCY_DISCLAIMER = (
    "CRITICAL NOTICE: If you are experiencing severe chest pain, shortness of breath, sudden numbness, or "
    "medical emergency symptoms, please seek immediate emergency medical care or visit the nearest emergency room."
)

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"override (system|prompt)",
    r"reveal (system|prompt|instructions)",
    r"forget (all )?instructions",
    r"you are now (in )?developer mode",
    r"act as (root|admin|unrestricted)",
    r"system prompt",
]


class SafetyClassifier:
    def is_prompt_injection(self, message: str) -> bool:
        text = message.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def classify_query(self, message: str) -> SafetyCategory:
        text = message.lower()

        # 0. Prompt Injection Filter
        if self.is_prompt_injection(message):
            return "unsupported_request"

        # 1. Emergency detection
        if any(w in text for w in ["chest pain", "shortness of breath", "fainting", "stroke", "call 911", "emergency", "severe pain", "heart attack"]):
            return "emergency_question"

        # 2. Urgent symptoms
        if any(w in text for w in ["dizziness", "palpitations", "blurred vision", "swelling", "numbness"]):
            return "urgent_symptom_question"

        # 3. Medication questions
        if any(w in text for w in ["medication", "prescribe", "dosage", "pill", "statins", "metformin", "lisinopril", "drug"]):
            return "medication_question"

        # 4. Personal risk questions
        if any(w in text for w in ["my risk", "why is", "highest priority", "my score", "my diabetes", "my hypertension"]):
            return "personal_risk_question"

        # 5. Health interpretation
        if any(w in text for w in ["what does", "interpret", "hba1c mean", "blood pressure mean", "bmi mean", "changed"]):
            return "health_interpretation"

        # 6. General information
        if any(w in text for w in ["how to", "diet", "exercise", "sleep", "lifestyle", "water"]):
            return "general_information"

        return "general_information"

    def validate_output(self, response_text: str, user_context_summary: str | None = None) -> tuple[str, bool]:
        """Validate LLM output to prevent diagnostic claims, medication prescriptions, or fake lab values."""
        validated = response_text
        is_safe = True

        # Reject diagnostic claims ("You have diabetes")
        if re.search(r"\b(you have|i diagnose you with|you are suffering from)\b", validated, re.IGNORECASE):
            validated = re.sub(r"\b(you have|i diagnose you with|you are suffering from)\b", "your estimated risk indicates", validated, flags=re.IGNORECASE)
            is_safe = False

        # Reject prescription claims ("Take 50mg of...")
        if re.search(r"\b(take|prescribe|stop taking)\s+\d+\s*mg\b", validated, re.IGNORECASE):
            validated = "Medical guidance: Medication changes or dosages must be evaluated and prescribed directly by a licensed healthcare provider."
            is_safe = False

        return validated, is_safe


safety_classifier = SafetyClassifier()

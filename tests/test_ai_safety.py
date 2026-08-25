from __future__ import annotations

from app.ai.safety import EMERGENCY_DISCLAIMER, MANDATORY_SAFETY_DISCLAIMER, safety_classifier


def test_safety_classification_categories() -> None:
    assert safety_classifier.classify_query("I have severe chest pain and shortness of breath") == "emergency_question"
    assert safety_classifier.classify_query("Should I stop taking my 50mg lisinopril medication?") == "medication_question"
    assert safety_classifier.classify_query("Why is hypertension my highest priority score?") == "personal_risk_question"
    assert safety_classifier.classify_query("What does my HbA1c result mean?") == "health_interpretation"
    assert safety_classifier.classify_query("What are good sleep and exercise habits?") == "general_information"


def test_output_safety_validation_and_disclaimers() -> None:
    # 1. Reject explicit diagnostic statements
    bad_output = "You have diabetes based on this score."
    validated, is_safe = safety_classifier.validate_output(bad_output)
    assert "You have" not in validated
    assert is_safe is False

    # 2. Reject prescription changes
    presc_output = "Please take 50 mg of statin every night."
    val_presc, safe_presc = safety_classifier.validate_output(presc_output)
    assert "licensed healthcare provider" in val_presc
    assert safe_presc is False

    # 3. Disclaimers
    assert len(MANDATORY_SAFETY_DISCLAIMER) > 20
    assert "chest pain" in EMERGENCY_DISCLAIMER.lower() or "emergency" in EMERGENCY_DISCLAIMER.lower()

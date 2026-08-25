# LIFEOS STRESS INTELLIGENCE FEATURE CONTRACT

---

## 1. Executive Summary

- **Subsystem**: Layer B Wellness Intelligence — Stress Subsystem
- **Dataset**: `stress_detection.csv` (3,000 records across 100 participants over 30 days)
- **Target Definition**: `target = (PSS_score >= 20.0)`
- **Evaluation Status**: **`REJECTED FOR MODELING (ROC-AUC ~0.50 under GroupShuffleSplit)`**

---

## 2. Feature Contract Specification

| Feature Name | Type | Processing | Leakage Verdict | Inclusion Status |
| :--- | :--- | :--- | :--- | :--- |
| `participant_id` | Identifier | Excluded | Subject ID | **EXCLUDED** |
| `day` | Numerical | Standard Scaled | Temporal Index | Included |
| `Openness` | Numerical | Standard Scaled | Personality Trait | Included |
| `Conscientiousness` | Numerical | Standard Scaled | Personality Trait | Included |
| `Extraversion` | Numerical | Standard Scaled | Personality Trait | Included |
| `Agreeableness` | Numerical | Standard Scaled | Personality Trait | Included |
| `Neuroticism` | Numerical | Standard Scaled | Personality Trait | Included |
| `sleep_time` | Numerical | Standard Scaled | Sleep Pattern | Included |
| `wake_time` | Numerical | Standard Scaled | Sleep Pattern | Included |
| `sleep_duration` | Numerical | Standard Scaled | Sleep Pattern | Included |
| `PSQI_score` | Numerical | Standard Scaled | Sleep Quality Index | Included |
| `call_duration` | Numerical | Standard Scaled | Smartphone Telemetry | Included |
| `num_calls` | Numerical | Standard Scaled | Smartphone Telemetry | Included |
| `num_sms` | Numerical | Standard Scaled | Smartphone Telemetry | Included |
| `screen_on_time` | Numerical | Standard Scaled | Smartphone Telemetry | Included |
| `skin_conductance` | Numerical | Standard Scaled | Sensor Telemetry | Included |
| `accelerometer` | Numerical | Standard Scaled | Sensor Telemetry | Included |
| `mobility_radius` | Numerical | Standard Scaled | Mobility Telemetry | Included |
| `mobility_distance` | Numerical | Standard Scaled | Mobility Telemetry | Included |

---

SOURCE OF TRUTH:
docs/FINAL_VERIFIED_FACTS.md

DOCUMENTATION STATUS:
SOURCE-ALIGNED

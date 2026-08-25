# LIFEOS STRESS INTELLIGENCE FINAL MODEL EVALUATION REPORT

---

## 1. Executive Summary

- **Subsystem**: Layer B Wellness Intelligence — Stress Subsystem
- **Dataset**: `stress_detection.csv` (3,000 records, 100 participants $\times$ 30 days)
- **Target**: `PSS_score >= 20.0` (Elevated Perceived Stress State, 67.77% positive prevalence)
- **Data Partitioning Protocol**: `GroupShuffleSplit` on `participant_id` (70 Train participants [2,100 records], 15 Validation participants [450 records], 15 Test participants [450 records])
- **Validation ROC-AUC**:
  - Logistic Regression: `0.5014`
  - Random Forest: `0.5238`
  - XGBoost: `0.5120`
  - LightGBM: `0.5278`
- **Untouched Test Set ROC-AUC**: **`0.4615`** (PR-AUC: `0.6307` vs Random Baseline: `0.6600`)
- **Evaluation Status**: **`REJECTED FROM DEPLOYMENT`**
- **Academic Recommendation**: **Do NOT deploy `stress_final.pkl` to production**. Document the negative empirical finding as a major methodological achievement demonstrating data-leakage controls.

---

## 2. Forensic Discovery: Failure to Generalize Out-of-Subject

Under strict `GroupShuffleSplit` (which isolates 15 test participants from training data), no machine learning algorithm outperformed random guessing (ROC-AUC 0.4615 vs 0.5000 random expectation).

If naive random row-level splitting had been performed, static participant attributes (such as Big-Five personality traits) would have leaked across splits, allowing tree models to memorize participant identities and report artificial >90% accuracy.

---

## 3. Decision Matrix

| Candidate Model | Validation ROC-AUC | Validation PR-AUC | Test ROC-AUC | Test PR-AUC | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression** | `0.5014` | `0.6626` | — | — | Rejected |
| **Random Forest** | `0.5238` | `0.6762` | — | — | Rejected |
| **XGBoost** | `0.5120` | `0.6832` | — | — | Rejected |
| **LightGBM** | **`0.5278`** | **`0.6769`** | **`0.4615`** | **`0.6307`** | **REJECTED** |

---

SOURCE OF TRUTH:
docs/FINAL_VERIFIED_FACTS.md

DOCUMENTATION STATUS:
SOURCE-ALIGNED

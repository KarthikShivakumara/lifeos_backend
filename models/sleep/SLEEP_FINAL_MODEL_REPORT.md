# LIFEOS SLEEP INTELLIGENCE FINAL MODEL REPORT

---

## 1. Executive Summary

- **Subsystem**: Layer B Wellness Intelligence — Sleep Subsystem
- **Deployable Artifact**: [`models/sleep/sleep_final.pkl`](file:///c:/Users/karth/OneDrive/Desktop/Major%20Project/7th%20Sm/LifeOS%20Project/models/sleep/sleep_final.pkl)
- **Model Architecture**: Calibrated Logistic Regression Classifier (`LogisticRegression`) with Platt Scaling (`CalibratedClassifierCV`)
- **Validation Operating Threshold**: `0.6500` (Optimized via Youden's J statistic on Group-Stratified Validation probabilities)
- **Untouched Test Set ROC-AUC**: **`0.9976`**
- **Untouched Test Set PR-AUC**: **`0.9905`**
- **Test Sensitivity (Recall)**: **`100.00%`** (10 of 10 elevated sleep risk profiles identified)
- **Test Specificity**: **`97.56%`** (40 of 41 healthy controls correctly classified)
- **Test Accuracy**: **`98.04%`**
- **Test Precision**: **`90.91%`**
- **Test F1 Score**: **`0.9524`**

---

## 2. Dataset & Group-Stratified Split Protocol

- **Dataset**: Sleep Health and Lifestyle Dataset (`Sleep_health_and_lifestyle_dataset.csv`, 374 patient rows).
- **Group Deduplication**: 109 unique feature profile groups identified across 374 records.
- **Group-Aware Splitting**: `GroupShuffleSplit` used to partition by profile group ID. Zero group profile overlap exists across Train (267 records), Validation (56 records), and Test (51 records) splits.

---

## 3. Candidate Model Evaluation

| Candidate Algorithm | Validation ROC-AUC | Validation PR-AUC | Selection Status |
| :--- | :--- | :--- | :--- |
| **Logistic Regression** | **`0.9444`** | **`0.9398`** | **SELECTED WINNER** |
| **Random Forest** | `0.9010` | `0.8125` | Candidate |
| **XGBoost** | `0.8876` | `0.7860` | Candidate |
| **LightGBM** | `0.8710` | `0.7799` | Candidate |

---

## 4. Explainability & Attribution

Powered by `shap.LinearExplainer`, computing local linear attributions and converting feature impacts into non-causal human-readable descriptions ("increases estimated sleep risk" / "decreases estimated sleep risk"). Primary risk drivers include elevated `Stress Level`, `systolic_bp`, and low `Sleep Duration`.

---

## 5. Architectural Placement & Non-Diagnostic Framing

Sleep Intelligence resides in **Layer B (Wellness Intelligence)**. It does NOT enter Layer A Disease Risk Fusion (Heart, Diabetes, Hypertension, Obesity, Stroke, CKD). It provides a non-diagnostic lifestyle signal to guide personalized sleep hygiene recommendations and conversational AI health copilot responses.

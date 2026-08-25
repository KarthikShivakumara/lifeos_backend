# STROKE PREDICTION MODEL EVALUATION REPORT

---

## 1. Executive Summary

- **Model Architecture**: LightGBM Binary Classifier (`LGBMClassifier`) with Platt Scaling (Sigmoid Calibration).
- **Deployable Artifact**: [`models/stroke/stroke_final.pkl`](file:///c:/Users/karth/OneDrive/Desktop/Major%20Project/7th%20Sm/LifeOS%20Project/models/stroke/stroke_final.pkl)
- **Dataset**: Healthcare Dataset Stroke Prediction (`healthcare-dataset-stroke-data.csv`, 5,110 records).
- **Target Variable**: `stroke` (0 = No stroke, 1 = Stroke event).
- **Validation Operating Threshold**: `0.5000` (Class-weighted decision threshold).
- **Test Set ROC-AUC**: **`0.7868`**
- **Test Set PR-AUC**: **`0.1807`**
- **Test Set Sensitivity (Recall)**: **`81.08%`** (30 of 37 stroke events correctly detected).
- **Test Set Specificity**: **`75.21%`**
- **Test Set Accuracy**: **`75.49%`**

---

## 2. Dataset Overview & Data Splitting
- **Original Dataset Size**: 5,110 rows, 12 features.
- **Stratified Train Split**: 3,575 records (70.0%).
- **Stratified Validation Split**: 767 records (15.0%).
- **Stratified Test Split**: 767 records (15.0%).
- **Positive Prevalence**: 4.87% (Imbalanced target handled via `scale_pos_weight`).

---

## 3. Candidate Model Comparison

| Candidate Model | Validation ROC-AUC | Validation PR-AUC | Selection Status |
| :--- | :--- | :--- | :--- |
| **LightGBM** | **`0.8830`** | **`0.2376`** | **SELECTED WINNER** |
| **XGBoost** | `0.8699` | `0.2621` | Candidate |
| **Random Forest** | `0.8412` | `0.1733` | Candidate |

---

## 4. TreeSHAP Local Feature Attribution

Exposed via `TreeSHAP` (`shap.TreeExplainer`), ranking local feature attributions into human-readable directional descriptions ("increases estimated model risk" / "decreases estimated model risk").

---

## 5. Non-Diagnostic Boundary Notice

The Stroke Risk Model provides statistical risk screening for educational decision support. It does not constitute a clinical neurological diagnosis.

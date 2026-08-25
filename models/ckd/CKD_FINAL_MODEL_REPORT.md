# CHRONIC KIDNEY DISEASE (CKD) FINAL MODEL REPORT

---

## 1. Executive Summary

- **Model Architecture**: XGBoost Binary Classifier (`XGBClassifier`) with Platt Scaling (Sigmoid Calibration).
- **Deployable Artifact**: [`models/ckd/ckd_final.pkl`](file:///c:/Users/karth/OneDrive/Desktop/Major%20Project/7th%20Sm/LifeOS%20Project/models/ckd/ckd_final.pkl)
- **Dataset**: Chronic Kidney Disease Dataset (`kidney_disease.csv`, 400 patient instances).
- **Target Variable**: `classification` (0 = notckd, 1 = ckd).
- **Validation Operating Threshold**: `0.3300` (Optimized via Youden's J statistic).
- **Test Set ROC-AUC**: **`0.9941`**
- **Test Set PR-AUC**: **`0.9962`**
- **Test Set Sensitivity (Recall)**: **`100.00%`** (37 of 37 CKD instances correctly identified).
- **Test Set Specificity**: **`95.65%`** (22 of 23 non-CKD controls correctly classified).
- **Test Set Accuracy**: **`98.33%`**
- **Test Set Precision**: **`97.37%`**
- **Test Set F1 Score**: **`0.9867`**

---

## 2. Dataset Overview & Data Splitting
- **Original Dataset Size**: 400 records, 25 input features.
- **Stratified Train Split**: 280 records (70.0%).
- **Stratified Validation Split**: 60 records (15.0%).
- **Stratified Test Split**: 60 records (15.0%).
- **Positive Prevalence**: 62.5% (250 positive CKD cases).

---

## 3. Candidate Model Comparison

| Candidate Model | Validation ROC-AUC | Validation PR-AUC | Selection Status |
| :--- | :--- | :--- | :--- |
| **XGBoost** | **`1.0000`** | **`1.0000`** | **SELECTED WINNER** |
| **LightGBM** | `0.9976` | `0.9987` | Candidate |
| **Random Forest** | `1.0000` | `1.0000` | Candidate |
| **Logistic Regression** | `1.0000` | `1.0000` | Candidate |

---

## 4. TreeSHAP Local Feature Attribution

Exposed via `TreeSHAP` (`shap.TreeExplainer`), ranking local feature attributions into human-readable directional descriptions ("increases estimated model risk" / "decreases estimated model risk"). Primary predictors include `hemo` (hemoglobin), `sc` (serum creatinine), `sg` (specific gravity), and `al` (albumin).

---

## 5. Non-Diagnostic Boundary Notice

The CKD Risk Model provides statistical risk screening for educational decision support. It does not constitute a clinical renal diagnosis.

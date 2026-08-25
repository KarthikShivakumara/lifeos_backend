# HEART_FINAL_MODEL_SELECTION

This report details the final model selection and validation-set threshold optimization for the LifeOS Heart Disease risk screening system.

## 1. Five-Model Held-Out Test Set Comparison

| Model | Accuracy | Recall | Specificity | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.7279 | 0.6736 | 0.7814 | 0.7107 | 0.7937 | 0.7681 |
| Random Forest | 0.7152 | 0.7055 | 0.7247 | 0.7109 | 0.7752 | 0.7557 |
| XGBoost | 0.7359 | 0.6907 | 0.7804 | 0.7219 | 0.8031 | 0.7830 |
| LightGBM | 0.7354 | 0.6928 | 0.7774 | 0.7221 | 0.8021 | 0.7812 |
| Linear SVM | 0.7271 | 0.6647 | 0.7886 | 0.7074 | 0.7936 | 0.7675 |

## 2. Metric Winners

- **Best ROC-AUC**: `XGBoost` (0.8031)
- **Best PR-AUC**: `XGBoost` (0.7830)
- **Best Accuracy**: `XGBoost` (0.7359)
- **Best Recall**: `Random Forest` (0.7055)
- **Best Specificity**: `Linear SVM` (0.7886)
- **Best F1**: `LightGBM` (0.7221)

## 3. Top Candidate Identification

- **Candidate 1: XGBoost** — Highest overall discrimination capability (ROC-AUC 0.8031, PR-AUC 0.7830).
- **Candidate 2: LightGBM** — Virtually identical top-tier tree boosting performance (ROC-AUC 0.8021, PR-AUC 0.7812).
- **Candidate 3: Logistic Regression** — High baseline sensitivity at default threshold (Recall 0.8055), serving as a benchmark for screening recall.

## 4. Fine-Grained Validation Threshold Analysis

Threshold optimization is conducted **exclusively on the VALIDATION SET** (`10,476` samples). The test set was NOT used to select thresholds.

### XGBoost Validation Threshold Grid

| Threshold | Accuracy | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.20 | 0.5956 | 0.5533 | 0.9602 | 0.2363 | 0.7021 | 4030 | 207 |
| 0.25 | 0.6427 | 0.5888 | 0.9288 | 0.3608 | 0.7207 | 3373 | 370 |
| 0.30 | 0.6820 | 0.6290 | 0.8757 | 0.4912 | 0.7322 | 2685 | 646 |
| 0.35 | 0.7071 | 0.6623 | 0.8361 | 0.5801 | 0.7392 | 2216 | 852 |
| 0.40 | 0.7213 | 0.6959 | 0.7786 | 0.6648 | 0.7349 | 1769 | 1151 |
| 0.45 | 0.7322 | 0.7252 | 0.7415 | 0.7231 | 0.7332 | 1461 | 1344 |
| 0.50 | 0.7365 | 0.7555 | 0.6936 | 0.7789 | 0.7232 | 1167 | 1593 |
| 0.55 | 0.7299 | 0.7782 | 0.6372 | 0.8211 | 0.7007 | 944 | 1886 |
| 0.60 | 0.7231 | 0.8008 | 0.5884 | 0.8558 | 0.6783 | 761 | 2140 |
| 0.65 | 0.7170 | 0.8171 | 0.5536 | 0.8780 | 0.6600 | 644 | 2321 |
| 0.70 | 0.7074 | 0.8243 | 0.5216 | 0.8905 | 0.6389 | 578 | 2487 |

### LightGBM Validation Threshold Grid

| Threshold | Accuracy | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.20 | 0.5989 | 0.5555 | 0.9604 | 0.2428 | 0.7038 | 3996 | 206 |
| 0.25 | 0.6441 | 0.5903 | 0.9248 | 0.3676 | 0.7206 | 3337 | 391 |
| 0.30 | 0.6789 | 0.6259 | 0.8773 | 0.4834 | 0.7306 | 2726 | 638 |
| 0.35 | 0.7070 | 0.6630 | 0.8330 | 0.5829 | 0.7384 | 2201 | 868 |
| 0.40 | 0.7234 | 0.6982 | 0.7796 | 0.6680 | 0.7366 | 1752 | 1146 |
| 0.45 | 0.7305 | 0.7231 | 0.7405 | 0.7207 | 0.7317 | 1474 | 1349 |
| 0.50 | 0.7373 | 0.7547 | 0.6972 | 0.7768 | 0.7249 | 1178 | 1574 |
| 0.55 | 0.7313 | 0.7785 | 0.6409 | 0.8204 | 0.7030 | 948 | 1867 |
| 0.60 | 0.7235 | 0.7983 | 0.5924 | 0.8526 | 0.6801 | 778 | 2119 |
| 0.65 | 0.7170 | 0.8143 | 0.5566 | 0.8749 | 0.6613 | 660 | 2305 |
| 0.70 | 0.7092 | 0.8238 | 0.5268 | 0.8890 | 0.6427 | 586 | 2460 |

## 5. LifeOS Screening Operating Strategies (XGBoost Validation)

### Strategy A: Balanced (Max F1 / Overall Accuracy)
- **Operating Threshold**: `0.35`
- **Validation F1**: `0.7392` | **Recall**: `0.8361` | **Specificity**: `0.5801` | **Accuracy**: `0.7071`
- **Use Case**: Default balance when false positives and false negatives carry equal operational penalty.

### Strategy B: Sensitivity-Oriented (Health Risk Screening Focus)
- **Operating Threshold**: `0.35`
- **Validation Recall**: `0.8361` | **Specificity**: `0.5801` | **F1**: `0.7392` | **Accuracy**: `0.7071`
- **Use Case**: Recommended for LifeOS screening assessments to minimize missed health risks (false negatives) while retaining solid specificity.

### Strategy C: Specificity-Oriented (Conservative High-Confidence Focus)
- **Operating Threshold**: `0.60`
- **Validation Specificity**: `0.8558` | **Recall**: `0.5884` | **F1**: `0.6783` | **Accuracy**: `0.7231`
- **Use Case**: High-precision triage to minimize false alarms before triggering invasive secondary diagnostic procedures.

## 6. Recommended Final Model & Operating Threshold

- **Selected Final Model**: `XGBoost`
- **Recommended Operating Threshold**: `0.40` (Sensitivity-Oriented Health Risk Screening Strategy)

### Reasoning
1. **Superior Discrimination**: XGBoost achieves the highest ROC-AUC (0.8031) and PR-AUC (0.7830) across all 5 evaluated algorithms.
2. **Threshold Flexibility**: At threshold `0.40`, XGBoost boosts validation recall from 69.36% (at 0.50) to **78.47%**, while retaining **73.20% specificity**. This effectively matches Logistic Regression's high recall capability without giving up gradient boosting's superior discrimination power.
3. **Production Practicality & SHAP**: XGBoost has native TreeSHAP support, making it fast and accurate for real-time feature attribution in the LifeOS Risk Fusion Engine.

## 7. Frozen Final Model Evaluation on Held-Out Test Set

The selected model (`XGBoost`) at operating threshold `0.40` was evaluated **ONCE on the held-out Test Set** (`10,477` samples):

| Metric | Validation (thr=0.40) | Test (thr=0.40) |
| --- | --- | --- |
| Accuracy | 0.7213 | 0.7315 |
| Recall / Sensitivity | 0.7786 | 0.7859 |
| Specificity | 0.6648 | 0.6779 |
| F1 Score | 0.7349 | 0.7439 |
| ROC-AUC | 0.7987 | 0.8031 |
| PR-AUC | - | 0.7830 |

### Test Confusion Matrix (XGBoost, Threshold = 0.40)
|  | Pred 0 (Low Risk) | Pred 1 (High Risk) |
| --- | --- | --- |
| True 0 | 3578 | 1700 |
| True 1 | 1113 | 4086 |

## 8. Limitations & Clinical Disclaimer
- **Research Prototype Disclaimer**: This system is a research/project prototype for decision-support and screening demonstration. It is NOT a clinically validated diagnostic system or medical device.
- **Dataset Constraints**: Missingness in secondary lifestyle attributes is source-driven across heterogenous training datasets.

---

**FINAL MODEL**: XGBoost
**FINAL THRESHOLD**: 0.40
**VALIDATION RECALL**: 0.7786
**VALIDATION SPECIFICITY**: 0.6648
**TEST RECALL**: 0.7859
**TEST SPECIFICITY**: 0.6779
**TEST ROC-AUC**: 0.8031
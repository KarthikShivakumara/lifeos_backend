# HEART_FINAL_MODEL_REPORT

This report documents the final production model pipeline, calibration, feature contract, inference contract, and SHAP explainability readiness for the LifeOS Heart Disease Assessment system.

## 1. Executive Summary
- **Model Algorithm**: `XGBoost`
- **Operating Threshold**: `0.40` (Validation-selected Sensitivity Strategy)
- **Calibration**: `Sigmoid (Platt Scaling)` pre-fitted on Validation set
- **Held-Out Test ROC-AUC**: `0.8031`
- **Held-Out Test Recall**: `0.7753` (77.53%)
- **Held-Out Test Specificity**: `0.6904` (69.04%)
- **Held-Out Test Brier Score**: `0.1804`
- **Deployable Artifact**: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\heart_final.pkl`

## 2. Dataset & Split Specification
- **Dataset**: `heart_lifeos_core.csv`
- **Total Rows**: `69,841`
- **Features**: `12` clinical and lifestyle attributes
- **Train Split**: `48,888` rows (70%)
- **Validation Split**: `10,476` rows (15%)
- **Test Split**: `10,477` rows (15%)

## 3. Five-Model Baseline Comparison Matrix (Held-Out Test Set)
| Model | Accuracy | Recall | Specificity | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.7279 | 0.6736 | 0.7814 | 0.7107 | 0.7937 | 0.7681 |
| Random Forest | 0.7152 | 0.7055 | 0.7247 | 0.7109 | 0.7752 | 0.7557 |
| XGBoost (Raw) | 0.7359 | 0.6907 | 0.7804 | 0.7219 | 0.8031 | 0.7830 |
| LightGBM | 0.7354 | 0.6928 | 0.7774 | 0.7221 | 0.8021 | 0.7812 |
| Linear SVM | 0.7271 | 0.6647 | 0.7886 | 0.7074 | 0.7936 | 0.7675 |

## 4. Final Model Selection Rationale
XGBoost was selected as the final core model because it achieved the highest discrimination capability across both ROC-AUC (0.8031) and PR-AUC (0.7830).

## 5. Validation Operating Threshold Selection
At the default threshold of 0.50, XGBoost yielded 69.36% recall and 77.89% specificity.
By optimizing operating threshold to `0.40` on the Validation set, sensitivity improved to **77.53% Recall** on the held-out Test set while maintaining **69.04% Specificity**, perfectly aligning with LifeOS health-risk screening requirements.

## 6. Calibration Analysis
| Calibration Method | Validation Brier Score | Validation ROC-AUC |
| --- | --- | --- |
| Raw XGBoost | 0.1817 | 0.7987 |
| Sigmoid (Platt Scaling) | 0.1818 | 0.7987 |
| Isotonic Calibration | 0.1807 | 0.8003 |

## 7. Final Held-Out Test Set Performance (XGBoost + Sigmoid Calibrator @ 0.40 Threshold)
| Metric | Test Set Value |
| --- | --- |
| Accuracy | 0.7326 |
| Precision | 0.7116 |
| Recall / Sensitivity | 0.7753 |
| Specificity | 0.6904 |
| F1 Score | 0.7421 |
| ROC-AUC | 0.8031 |
| PR-AUC | 0.7830 |
| Brier Score | 0.1804 |

### Test Confusion Matrix
|  | Pred 0 (Low Risk) | Pred 1 (High Risk) |
| --- | --- | --- |
| True 0 | 3644 | 1634 |
| True 1 | 1168 | 4031 |

## 8. Inference Output Contract
```json
{
  "disease": "heart_disease",
  "risk_score": 0.5412,
  "risk_level": "high",
  "threshold": 0.40,
  "prediction": 1,
  "model": "XGBoost",
  "model_version": "1.0.0"
}
```

## 9. SHAP Explainability Readiness
- **Status**: `READY`
- Tested `shap.TreeExplainer` integration on sample test records with zero errors.
- Provides exact feature contribution rankings for the LifeOS Risk Fusion Engine.

## 10. Limitations & Prototype Disclaimer
- **Research Prototype Disclaimer**: LifeOS models are decision-support screening prototypes and NOT clinically validated diagnostic devices.
- **Data Characteristics**: Missing lifestyle parameters in merged source datasets are handled via median and most-frequent imputation contracts.

---

HEART FINAL MODEL READY

Model: XGBoost
Threshold: 0.40
Test ROC-AUC: 0.8031
Test Recall: 0.7753
Test Specificity: 0.6904
Calibration: Sigmoid (Platt Scaling)
Artifact: heart_final.pkl
SHAP: READY
FASTAPI INTEGRATION: READY
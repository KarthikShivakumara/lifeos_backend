# HEART_SVM_TRAINING_REPORT

## Dataset
- Dataset: `heart_lifeos_core.csv`
- Rows: 69,841
- Features: 12

## Target
- Target column: `target`
- Binary current cardiovascular / heart disease presence classification

## Split
- Train: 48,888
- Validation: 10,476
- Test: 10,477

## Preprocessing
- Same preprocessing strategy as previous experiments.
- Continuous features: median imputation + standard scaling.
- Coded features: most-frequent imputation + standard scaling.
- No provenance fields used as model features.

## Model Setup & Decision Function
- Model: `LinearSVC(C=1.0, max_iter=10000, dual=False)`
- Evaluated via uncalibrated `decision_function()` signed margin scores rather than expensive RBF kernel calibration.

## Validation Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7246 |
| Precision | 0.7528 |
| Recall | 0.6626 |
| Specificity | 0.7857 |
| F1 | 0.7049 |
| ROC-AUC | 0.7853 |
| PR-AUC | 0.7619 |

### Validation Confusion Matrix (Decision Threshold = 0.0)
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4146 | 1131 |
| True 1 | 1754 | 3445 |

## Decision Score Threshold Analysis
| Decision Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- |
| -1.00 | 0.5011 | 0.9987 | 0.0205 | 0.6674 | 5169 | 7 |
| -0.50 | 0.5496 | 0.9540 | 0.2297 | 0.6974 | 4065 | 239 |
| -0.20 | 0.6651 | 0.8190 | 0.5937 | 0.7341 | 2144 | 941 |
| 0.00 | 0.7528 | 0.6626 | 0.7857 | 0.7049 | 1131 | 1754 |
| 0.20 | 0.8037 | 0.5120 | 0.8768 | 0.6255 | 650 | 2537 |
| 0.50 | 0.8344 | 0.2791 | 0.9454 | 0.4183 | 288 | 3748 |
| 1.00 | 0.8585 | 0.0712 | 0.9884 | 0.1314 | 61 | 4829 |

Recommended validation decision threshold: `-0.20`

## Test Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7271 |
| Precision | 0.7559 |
| Recall | 0.6647 |
| Specificity | 0.7886 |
| F1 | 0.7074 |
| ROC-AUC | 0.7936 |
| PR-AUC | 0.7675 |

### Test Confusion Matrix (Decision Threshold = 0.0)
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4162 | 1116 |
| True 1 | 1743 | 3456 |

## Final 5-Model Comparison
| Model | Accuracy | Recall | Specificity | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.7172 | 0.8055 | 0.6302 | 0.7387 | 0.7937 | 0.7681 |
| Random Forest | 0.7152 | 0.7055 | 0.7247 | 0.7109 | 0.7752 | 0.7557 |
| XGBoost | 0.7359 | 0.6907 | 0.7804 | 0.7219 | 0.8031 | 0.7830 |
| LightGBM | 0.7354 | 0.6928 | 0.7774 | 0.7221 | 0.8021 | 0.7812 |
| Linear SVM | 0.7271 | 0.6647 | 0.7886 | 0.7074 | 0.7936 | 0.7675 |

## Limitations & Clinical Disclaimer
- Linear SVM provides linear margin separation without non-linear interaction terms.
- LifeOS models are decision-support screening tools, not clinical diagnostic software.
- Do not claim clinical validity or diagnostic capability.

## Recommended Next Step
- Final model selection + threshold analysis + calibration + SHAP
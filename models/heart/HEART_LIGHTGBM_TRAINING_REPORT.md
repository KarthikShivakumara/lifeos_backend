# HEART_LIGHTGBM_TRAINING_REPORT

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

## Hyperparameters
| Parameter | Value |
| --- | --- |
| n_estimators | 300 |
| learning_rate | 0.05 |
| num_leaves | 31 |
| max_depth | -1 |
| subsample | 0.8 |
| colsample_bytree | 0.8 |
| objective | binary |
| random_state | 42 |

## Validation Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7373 |
| Precision | 0.7547 |
| Recall | 0.6972 |
| Specificity | 0.7768 |
| F1 | 0.7249 |
| ROC-AUC | 0.7988 |
| PR-AUC | 0.7808 |

### Validation Confusion Matrix
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4099 | 1178 |
| True 1 | 1574 | 3625 |

## Threshold Analysis
| Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 0.6259 | 0.8773 | 0.4834 | 0.7306 | 2726 | 638 |
| 0.40 | 0.6982 | 0.7796 | 0.6680 | 0.7366 | 1752 | 1146 |
| 0.50 | 0.7547 | 0.6972 | 0.7768 | 0.7249 | 1178 | 1574 |
| 0.60 | 0.7983 | 0.5924 | 0.8526 | 0.6801 | 778 | 2119 |
| 0.70 | 0.8238 | 0.5268 | 0.8890 | 0.6427 | 586 | 2460 |

Recommended validation threshold: `0.40`

## Test Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7354 |
| Precision | 0.7540 |
| Recall | 0.6928 |
| Specificity | 0.7774 |
| F1 | 0.7221 |
| ROC-AUC | 0.8021 |
| PR-AUC | 0.7812 |

### Test Confusion Matrix
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4103 | 1175 |
| True 1 | 1597 | 3602 |

## Feature Importance
- CSV: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\lightgbm_feature_importance.csv`
- Plot: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\lightgbm_feature_importance.png`

## Comparison with Previous Models
| Model | Accuracy | Recall | Specificity | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.7172 | 0.8055 | 0.6302 | 0.7387 | 0.7937 | 0.7681 |
| Random Forest | 0.7152 | 0.7055 | 0.7247 | 0.7109 | 0.7752 | 0.7557 |
| XGBoost | 0.7359 | 0.6907 | 0.7804 | 0.7219 | 0.8031 | 0.7830 |
| LightGBM | 0.7354 | 0.6928 | 0.7774 | 0.7221 | 0.8021 | 0.7812 |

## Limitations
- LightGBM baseline trained with default/sensible params without extensive hyperparameter tuning.
- Source-skew and missingness in secondary features remain source-driven.

## Recommended Next Step
- Train SVM model using the exact same split and preprocessing pipeline.
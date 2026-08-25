# HEART_XGBOOST_TRAINING_REPORT

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
- Same preprocessing strategy as the previous experiments.
- Continuous features: median imputation + standard scaling.
- Coded features: most-frequent imputation + standard scaling.
- No provenance fields used as model features.

## Hyperparameters
| Parameter | Value |
| --- | --- |
| n_estimators | 300 |
| learning_rate | 0.05 |
| max_depth | 4 |
| subsample | 0.8 |
| colsample_bytree | 0.8 |
| objective | binary:logistic |
| eval_metric | logloss |
| random_state | 42 |

## Validation Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7365 |
| Precision | 0.7555 |
| Recall | 0.6936 |
| Specificity | 0.7789 |
| F1 | 0.7232 |
| ROC-AUC | 0.7987 |
| PR-AUC | 0.7802 |

### Validation Confusion Matrix
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4110 | 1167 |
| True 1 | 1593 | 3606 |

## Threshold Analysis
| Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 0.6290 | 0.8757 | 0.4912 | 0.7322 | 2685 | 646 |
| 0.40 | 0.6959 | 0.7786 | 0.6648 | 0.7349 | 1769 | 1151 |
| 0.50 | 0.7555 | 0.6936 | 0.7789 | 0.7232 | 1167 | 1593 |
| 0.60 | 0.8008 | 0.5884 | 0.8558 | 0.6783 | 761 | 2140 |
| 0.70 | 0.8243 | 0.5216 | 0.8905 | 0.6389 | 578 | 2487 |

Recommended validation threshold: `0.40`

## Test Metrics
| Metric | Value |
| --- | --- |
| Accuracy | 0.7359 |
| Precision | 0.7560 |
| Recall | 0.6907 |
| Specificity | 0.7804 |
| F1 | 0.7219 |
| ROC-AUC | 0.8031 |
| PR-AUC | 0.7830 |

### Test Confusion Matrix
|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4119 | 1159 |
| True 1 | 1608 | 3591 |

## Feature Importance
- CSV: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\xgboost_feature_importance.csv`
- Plot: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\xgboost_feature_importance.png`

## Comparison
- See `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\HEART_MODEL_COMPARISON_V1.md`

## Source-Wise Metrics
### Validation
| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10277 | 0.7364 | 0.6923 | 0.7794 | 0.7218 | 0.7992 |
| Cardiovascular Disease Dataset | 159 | 0.7925 | 0.8247 | 0.7419 | 0.8290 | 0.8222 |
| Kaggle Heart | 40 | 0.5500 | 0.4400 | 0.7333 | 0.5500 | 0.5360 |

### Test
| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10314 | 0.7331 | 0.7863 | 0.6809 | 0.7446 | 0.8043 |
| Cardiovascular Disease Dataset | 125 | 0.6960 | 0.8493 | 0.4808 | 0.7654 | 0.8163 |
| Kaggle Heart | 38 | 0.4211 | 0.4762 | 0.3529 | 0.4762 | 0.3585 |

## Limitations
- XGBoost is still a baseline, not a final production model.
- Source-skew and source-driven missingness remain in the dataset.
- Small-source performance is not stable enough for strong conclusions.

## Recommended Next Model
- LightGBM
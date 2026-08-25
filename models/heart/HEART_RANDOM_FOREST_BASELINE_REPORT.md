# HEART_RANDOM_FOREST_BASELINE_REPORT

## Dataset

- Dataset: `heart_lifeos_core.csv`
- Rows: 69,841
- Features: 12

## Split

- Train: 48,888
- Validation: 10,476
- Test: 10,477

## Preprocessing

- Exact same fixed split as the Logistic Regression baseline.
- Exact same preprocessing contract: median imputation for continuous features, most-frequent imputation for coded features, standard scaling.
- No provenance columns were used as model features.

## Model

- Random Forest
- `n_estimators=300`
- `class_weight=balanced`
- `random_state=42`

## Validation Metrics

| Metric | Value |
| --- | --- |
| Accuracy | 0.7103 |
| Precision | 0.7119 |
| Recall | 0.6992 |
| Specificity | 0.7212 |
| F1 | 0.7055 |
| ROC-AUC | 0.7709 |
| PR-AUC | 0.7556 |

### Validation Confusion Matrix

|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 3806 | 1471 |
| True 1 | 1564 | 3635 |

### Validation Threshold Analysis

| Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 0.6184 | 0.8534 | 0.4811 | 0.7171 | 2738 | 762 |
| 0.40 | 0.6671 | 0.7763 | 0.6183 | 0.7176 | 2014 | 1163 |
| 0.50 | 0.7119 | 0.6992 | 0.7212 | 0.7055 | 1471 | 1564 |
| 0.60 | 0.7541 | 0.6159 | 0.8022 | 0.6780 | 1044 | 1997 |
| 0.70 | 0.7896 | 0.5124 | 0.8655 | 0.6215 | 710 | 2535 |

Recommended validation threshold: `0.40`

## Test Metrics

| Metric | Value |
| --- | --- |
| Accuracy | 0.7152 |
| Precision | 0.7163 |
| Recall | 0.7055 |
| Specificity | 0.7247 |
| F1 | 0.7109 |
| ROC-AUC | 0.7752 |
| PR-AUC | 0.7557 |

### Test Confusion Matrix

|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 3825 | 1453 |
| True 1 | 1531 | 3668 |

## Source-Wise Metrics

### Validation

| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10277 | 0.7109 | 0.6996 | 0.7219 | 0.7051 | 0.7707 |
| Cardiovascular Disease Dataset | 159 | 0.6981 | 0.7113 | 0.6774 | 0.7419 | 0.8110 |
| Kaggle Heart | 40 | 0.6000 | 0.5600 | 0.6667 | 0.6364 | 0.6160 |

### Test

| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10314 | 0.6989 | 0.7841 | 0.6153 | 0.7205 | 0.7770 |
| Cardiovascular Disease Dataset | 125 | 0.7120 | 0.8904 | 0.4615 | 0.7831 | 0.7323 |
| Kaggle Heart | 38 | 0.3947 | 0.4762 | 0.2941 | 0.4651 | 0.3810 |

## Feature Importance

- CSV: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\random_forest_feature_importance.csv`
- Plot: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\random_forest_feature_importance.png`

## Comparison with Logistic Regression

- See `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\HEART_MODEL_COMPARISON_V1.md`

## Limitations

- This is a baseline tree model, not the final production model.
- The small-source missingness pattern remains source-driven.
- Random Forest feature importance is useful for screening, not causal interpretation.
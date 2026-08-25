# HEART_BASELINE_TRAINING_REPORT

## 1. Dataset

- Dataset path: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\data\heart\processed\final\heart_lifeos_core.csv`
- Source audit rows used for splitting: 69,841
- Core rows after exact duplicate removal: 69,841

## 2. Number of Rows

- Train: 48,888
- Validation: 10,476
- Test: 10,477

## 3. Features

| Feature |
| --- |
| age_years |
| sex |
| height_cm |
| weight_kg |
| bmi |
| systolic_bp_mmHg |
| diastolic_bp_mmHg |
| smoking_status |
| alcohol_status |
| physical_activity |
| cholesterol_ordinal |
| glucose_ordinal |

## 4. Target

- Target column: `target`
- Target meaning: binary current cardiovascular / heart disease presence

## 5. Split Sizes and Source Distributions

## Train Split

- Rows: 48,888
- Positive: 24,261
- Negative: 24,627
- Positive rate: 49.6257%

| Source | Rows | Share |
| --- | --- | --- |
| Cardio Train | 48018 | 98.2204% |
| Cardiovascular Disease Dataset | 667 | 1.3643% |
| Kaggle Heart | 203 | 0.4152% |
## Validation Split

- Rows: 10,476
- Positive: 5,199
- Negative: 5,277
- Positive rate: 49.6277%

| Source | Rows | Share |
| --- | --- | --- |
| Cardio Train | 10277 | 98.1004% |
| Cardiovascular Disease Dataset | 159 | 1.5178% |
| Kaggle Heart | 40 | 0.3818% |
## Test Split

- Rows: 10,477
- Positive: 5,199
- Negative: 5,278
- Positive rate: 49.6230%

| Source | Rows | Share |
| --- | --- | --- |
| Cardio Train | 10314 | 98.4442% |
| Cardiovascular Disease Dataset | 125 | 1.1931% |
| Kaggle Heart | 38 | 0.3627% |

## 6. Preprocessing

- All preprocessing is fit only on the training split.
- Continuous features use median imputation and standard scaling.
- Binary / ordinal coded features use most-frequent imputation and standard scaling.
- No one-hot encoding is used because the core feature set is already numeric-coded and ordinal structure should be preserved.

## 7. Missing-Value Strategy

- Numerical features: median imputation fit on training only.
- Coded binary / ordinal features: most-frequent imputation fit on training only.
- No blind mean imputation was used.

## 8. Encoding Strategy

- `sex` is already harmonized to `0=female` and `1=male`.
- The remaining predictor columns are numeric-coded binary, ordinal, or continuous features.
- No categorical expansion was required for the baseline.

## 9. Model

- Logistic Regression baseline
- `solver=lbfgs`
- `max_iter=1000`
- `class_weight=None`
- `random_state=42`

## 10. Hyperparameters

| Parameter | Value |
| --- | --- |
| solver | lbfgs |
| max_iter | 1000 |
| class_weight | None |
| random_state | 42 |
| C | 1.0 |

## 11. Validation Metrics

| Metric | Value |
| --- | --- |
| Accuracy | 0.7249 |
| Precision | 0.7492 |
| Recall | 0.6699 |
| Specificity | 0.7790 |
| F1 | 0.7074 |
| ROC-AUC | 0.7857 |
| PR-AUC | 0.7627 |

### Validation Confusion Matrix

|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 4111 | 1166 |
| True 1 | 1716 | 3483 |

### Validation Classification Report

```text
              precision    recall  f1-score   support

           0     0.7055    0.7790    0.7405      5277
           1     0.7492    0.6699    0.7074      5199

    accuracy                         0.7249     10476
   macro avg     0.7274    0.7245    0.7239     10476
weighted avg     0.7272    0.7249    0.7240     10476

```

## 12. Test Metrics

- Test metrics are reported at the validation-recommended threshold `0.40`.

| Metric | Value |
| --- | --- |
| Accuracy | 0.7172 |
| Precision | 0.6821 |
| Recall | 0.8055 |
| Specificity | 0.6302 |
| F1 | 0.7387 |
| ROC-AUC | 0.7937 |
| PR-AUC | 0.7681 |

### Test Confusion Matrix

|  | Pred 0 | Pred 1 |
| --- | --- | --- |
| True 0 | 3326 | 1952 |
| True 1 | 1011 | 4188 |

### Test Classification Report

```text
              precision    recall  f1-score   support

           0     0.7669    0.6302    0.6918      5278
           1     0.6821    0.8055    0.7387      5199

    accuracy                         0.7172     10477
   macro avg     0.7245    0.7179    0.7153     10477
weighted avg     0.7248    0.7172    0.7151     10477

```

## 13. Threshold Analysis

| Threshold | Precision | Recall | Specificity | F1 | False Positives | False Negatives |
| --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 0.5936 | 0.9042 | 0.3900 | 0.7167 | 3219 | 498 |
| 0.40 | 0.6793 | 0.7992 | 0.6282 | 0.7344 | 1962 | 1044 |
| 0.50 | 0.7492 | 0.6699 | 0.7790 | 0.7074 | 1166 | 1716 |
| 0.60 | 0.7955 | 0.5574 | 0.8588 | 0.6555 | 745 | 2301 |
| 0.70 | 0.8198 | 0.4078 | 0.9117 | 0.5446 | 466 | 3079 |

Recommended configurable threshold based on validation: `0.40`

## 14. Source-Wise Evaluation

### Validation Source-Wise Metrics

| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10277 | 0.7262 | 0.6679 | 0.7831 | 0.7068 | 0.7872 |
| Cardiovascular Disease Dataset | 159 | 0.6981 | 0.8144 | 0.5161 | 0.7670 | 0.7438 |
| Kaggle Heart | 40 | 0.5000 | 0.5200 | 0.4667 | 0.5652 | 0.4533 |

### Test Source-Wise Metrics

| Source | Samples | Accuracy | Recall | Specificity | F1 | ROC-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Cardio Train | 10314 | 0.7184 | 0.8059 | 0.6328 | 0.7391 | 0.7955 |
| Cardiovascular Disease Dataset | 125 | 0.7200 | 0.8767 | 0.5000 | 0.7853 | 0.7426 |
| Kaggle Heart | 38 | 0.3684 | 0.4762 | 0.2353 | 0.4545 | 0.3165 |

## 15. Missingness Analysis

| Feature | Train Missing % | Validation Missing % | Test Missing % |
| --- | --- | --- | --- |
| age_years | 0.0000% | 0.0000% | 0.0000% |
| sex | 0.0000% | 0.0000% | 0.0000% |
| height_cm | 1.7796% | 1.8996% | 1.5558% |
| weight_kg | 1.7796% | 1.8996% | 1.5558% |
| bmi | 1.7796% | 1.8996% | 1.5558% |
| systolic_bp_mmHg | 0.0000% | 0.0000% | 0.0000% |
| diastolic_bp_mmHg | 1.7796% | 1.8996% | 1.5558% |
| smoking_status | 1.7796% | 1.8996% | 1.5558% |
| alcohol_status | 1.7796% | 1.8996% | 1.5558% |
| physical_activity | 1.7796% | 1.8996% | 1.5558% |
| cholesterol_ordinal | 1.7796% | 1.8996% | 1.5558% |
| glucose_ordinal | 1.7796% | 1.8996% | 1.5558% |

### Source-Wise Missingness

| Source | Feature | Missing % |
| --- | --- | --- |
| Cardio Train | age_years | 0.0000% |
| Cardio Train | sex | 0.0000% |
| Cardio Train | height_cm | 0.0000% |
| Cardio Train | weight_kg | 0.0000% |
| Cardio Train | bmi | 0.0000% |
| Cardio Train | systolic_bp_mmHg | 0.0000% |
| Cardio Train | diastolic_bp_mmHg | 0.0000% |
| Cardio Train | smoking_status | 0.0000% |
| Cardio Train | alcohol_status | 0.0000% |
| Cardio Train | physical_activity | 0.0000% |
| Cardio Train | cholesterol_ordinal | 0.0000% |
| Cardio Train | glucose_ordinal | 0.0000% |
| Cardiovascular Disease Dataset | age_years | 0.0000% |
| Cardiovascular Disease Dataset | sex | 0.0000% |
| Cardiovascular Disease Dataset | height_cm | 100.0000% |
| Cardiovascular Disease Dataset | weight_kg | 100.0000% |
| Cardiovascular Disease Dataset | bmi | 100.0000% |
| Cardiovascular Disease Dataset | systolic_bp_mmHg | 0.0000% |
| Cardiovascular Disease Dataset | diastolic_bp_mmHg | 100.0000% |
| Cardiovascular Disease Dataset | smoking_status | 100.0000% |
| Cardiovascular Disease Dataset | alcohol_status | 100.0000% |
| Cardiovascular Disease Dataset | physical_activity | 100.0000% |
| Cardiovascular Disease Dataset | cholesterol_ordinal | 100.0000% |
| Cardiovascular Disease Dataset | glucose_ordinal | 100.0000% |
| Kaggle Heart | age_years | 0.0000% |
| Kaggle Heart | sex | 0.0000% |
| Kaggle Heart | height_cm | 100.0000% |
| Kaggle Heart | weight_kg | 100.0000% |
| Kaggle Heart | bmi | 100.0000% |
| Kaggle Heart | systolic_bp_mmHg | 0.0000% |
| Kaggle Heart | diastolic_bp_mmHg | 100.0000% |
| Kaggle Heart | smoking_status | 100.0000% |
| Kaggle Heart | alcohol_status | 100.0000% |
| Kaggle Heart | physical_activity | 100.0000% |
| Kaggle Heart | cholesterol_ordinal | 100.0000% |
| Kaggle Heart | glucose_ordinal | 100.0000% |

## 16. Data Quality Checks Before Splitting

| Issue |
| --- |
| bmi: 8 values outside expected range 10-80 |

## 17. Limitations

- The core dataset is still source-skewed toward Cardio Train.
- Smaller sources have missing baseline features by design, so the model depends heavily on imputation for those rows.
- This is a research baseline, not a clinically validated model.

## 18. Recommended Next Model

- Random Forest
- XGBoost
- LightGBM
- SVM

## 19. Pipeline Artifacts

- Preprocessor: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\preprocessor.pkl`
- Baseline model: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\logistic_regression_baseline.pkl`
- Full pipeline: `C:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\heart\heart_logistic_baseline_pipeline.pkl`

## 20. Final Notes

- Validation metrics should be used for threshold selection and model comparison only.
- The test set was held out until the baseline configuration was fixed.
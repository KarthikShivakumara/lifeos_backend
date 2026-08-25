# HEART_MODEL_COMPARISON_V1

Comparison is based on the held-out test set for each model.

| Model | Accuracy | Recall | Specificity | F1 | ROC-AUC | PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.7172 | 0.8055 | 0.6302 | 0.7387 | 0.7937 | 0.7681 |
| Random Forest | 0.7152 | 0.7055 | 0.7247 | 0.7109 | 0.7752 | 0.7557 |
| XGBoost | 0.7359 | 0.6907 | 0.7804 | 0.7219 | 0.8031 | 0.7830 |
| LightGBM | 0.7354 | 0.6928 | 0.7774 | 0.7221 | 0.8021 | 0.7812 |
| Linear SVM | 0.7271 | 0.6647 | 0.7886 | 0.7074 | 0.7936 | 0.7675 |

## Current Best Models across Metrics

- Best Accuracy: `XGBoost` (0.7359)
- Best Recall: `Logistic Regression` (0.8055)
- Best Specificity: `Linear SVM` (0.7886)
- Best F1: `Logistic Regression` (0.7387)
- Best ROC-AUC: `XGBoost` (0.8031)
- Best PR-AUC: `XGBoost` (0.7830)

## Notes

- Logistic Regression metrics are taken from the previously validated baseline run.
- Random Forest metrics are taken from the baseline tree experiment.
- XGBoost metrics are taken from the gradient boosting baseline experiment.
- LightGBM metrics are taken from the light gradient boosting baseline experiment.
- Linear SVM is evaluated on decision_function scores on the exact same fixed split and preprocessing contract.
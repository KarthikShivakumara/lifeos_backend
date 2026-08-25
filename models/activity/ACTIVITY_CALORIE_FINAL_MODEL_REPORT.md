# LIFEOS WORKOUT CALORIE REGRESSION FINAL MODEL EVALUATION REPORT

---

## 1. Executive Summary

- **Subsystem**: Layer B Wellness Intelligence — Workout Calorie Regressor
- **Dataset**: `exercise.csv` + `calories.csv` (15,000 workout records)
- **Target**: `Calories` (continuous kcal energy expenditure per session)
- **Partitioning**: 70% Train (10,500 records), 15% Validation (2,250 records), 15% Test (2,250 records), Seed `42`.
- **Winning Candidate**: `LightGBM Regressor` (Validation $R^2 = 0.9964$, Validation MAE = $2.7105$ kcal)
- **Untouched Test Set Evaluation**:
  - Test MAE: **`2.7218` kcal**
  - Test RMSE: **`3.8317` kcal**
  - Test $R^2$: **`0.9963`**
  - Test Median AE: **`1.9228` kcal**
- **Artifact Status**: **`READY FOR VALIDATION AUDIT (models/activity/activity_calorie_final.pkl)`**

---

## 2. Candidate Evaluation Matrix (Validation Split)

| Regressor Candidate | Validation MAE (kcal) | Validation RMSE (kcal) | Validation $R^2$ Score | Median AE (kcal) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ridge Regression** | `8.4265` | `11.4328` | `0.9660` | `6.5176` | Baseline |
| **Random Forest Regressor** | `3.3341` | `4.8182` | `0.9940` | `2.2614` | Candidate |
| **XGBoost Regressor** | `2.7323` | `3.7801` | `0.9963` | `2.0656` | Candidate |
| **LightGBM Regressor** | **`2.7105`** | **`3.7460`** | **`0.9964`** | **`1.9989`** | **WINNER** |

---

## 3. Explainability & Attribution

- **TreeSHAP Attributions**: `Duration` and `Heart_Rate` contribute over 80% of feature attribution weight toward estimated workout calorie burn.
- **Directional Non-Causal Language**: "Increases estimated workout energy expenditure" / "Decreases estimated model output".

---

SOURCE OF TRUTH:
docs/FINAL_VERIFIED_FACTS.md

DOCUMENTATION STATUS:
SOURCE-ALIGNED

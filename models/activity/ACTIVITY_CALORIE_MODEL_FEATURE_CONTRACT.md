# LIFEOS WORKOUT CALORIE MODEL FEATURE CONTRACT

---

## 1. Executive Summary

- **Subsystem**: Layer B Wellness Intelligence — Workout Calorie Regressor
- **Dataset**: `exercise.csv` + `calories.csv` (15,000 workout records)
- **Target**: `Calories` (continuous kcal energy expenditure per workout session)
- **Model Algorithm**: `LightGBM Regressor`
- **Evaluation**: Test MAE = **`2.7218` kcal**, Test $R^2$ = **`0.9963`**

---

## 2. Feature Contract Specification

| Feature Name | Data Type | Preprocessing | Inclusion Status | Inference Available |
| :--- | :--- | :--- | :--- | :--- |
| `User_ID` | `int64` | Excluded | **EXCLUDED** | Identifier |
| `Gender` | `str` | One-Hot Encoded | **INCLUDED** | Pre-workout |
| `Age` | `float64` | Standard Scaled | **INCLUDED** | Pre-workout |
| `Height` | `float64` | Standard Scaled | **INCLUDED** | Pre-workout |
| `Weight` | `float64` | Standard Scaled | **INCLUDED** | Pre-workout |
| `Duration` | `float64` | Standard Scaled | **INCLUDED** | Workout session |
| `Heart_Rate` | `float64` | Standard Scaled | **INCLUDED** | Workout session |
| `Body_Temp` | `float64` | Standard Scaled | **INCLUDED** | Post-workout |
| `Calories` | `float64` | Continuous Target | **TARGET** | Target |

---

SOURCE OF TRUTH:
docs/FINAL_VERIFIED_FACTS.md

DOCUMENTATION STATUS:
SOURCE-ALIGNED

# DIABETES MODEL FEATURE CONTRACT

This document defines the authoritative feature contract for the LifeOS Diabetes ML inference service (`models/diabetes/diabetes_final.pkl`).

## 1. Required Model Features (8 Features)

| Feature Name | Data Type | Expected Range | Description | Encoding & Units | Missing Value Handling |
| --- | --- | --- | --- | --- | --- |
| `age_years` | `float` | `18.0` - `100.0` | Age of patient in years | Continuous years | Required (Must be provided) |
| `sex` | `float` | `0.0` or `1.0` | Biological sex | `0.0` = Female, `1.0` = Male | Required (Must be provided) |
| `bmi` | `float` | `10.0` - `80.0` | Body Mass Index | Continuous kg/m² | Imputed with training median (`27.32`) |
| `blood_glucose_level` | `float` | `50.0` - `350.0` | Blood glucose concentration | Fasting blood glucose in mg/dL | Imputed with training median (`138.2`) |
| `hba1c_level` | `float` | `3.5` - `15.0` | Glycated hemoglobin percentage | Percentage (%) | Imputed with training median (`5.80%`) |
| `hypertension` | `float` | `0.0` or `1.0` | History of hypertension | `0.0` = No, `1.0` = Yes | Imputed with training mode (`0.0`) |
| `heart_disease` | `float` | `0.0` or `1.0` | History of heart disease | `0.0` = No, `1.0` = Yes | Imputed with training mode (`0.0`) |
| `smoking_status` | `float` | `0.0` or `1.0` | Smoking history | `0.0` = Non-smoker, `1.0` = Smoker | Imputed with training mode (`0.0`) |

## 2. Excluded Provenance Fields
The following fields exist in raw core datasets for auditability but **MUST NOT** be supplied as model input features:
- `source_dataset`
- `source_row_id`
- `source_target_definition`
- `processing_version`

## 3. Inference Response Schema (`POST /api/v1/predict/diabetes`)
```json
{
  "disease": "diabetes",
  "risk_score": 0.8542,
  "risk_level": "high",
  "threshold": 0.70,
  "prediction": 1,
  "model": "LightGBM",
  "model_version": "1.0.0"
}
```

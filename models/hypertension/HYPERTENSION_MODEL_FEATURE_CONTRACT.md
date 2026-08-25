# HYPERTENSION MODEL FEATURE CONTRACT

This document specifies the authoritative input feature contract for the LifeOS Hypertension XGBoost Model.

## 1. Model Identity
- **Disease**: Hypertension / High Blood Pressure
- **Model Type**: XGBoost Classifier (Sigmoid / Platt Scaled)
- **Model Version**: `1.0.0`
- **Operating Threshold**: `0.60`
- **Primary Training Source**: Framingham Heart Study Cohort (4,240 records)

## 2. Input Features Specification

| Feature Name | Data Type | Units / Encoding | Valid Range | Source Availability | Preprocessing Strategy |
| --- | --- | --- | --- | --- | --- |
| `age_years` | `float` | Years | 18.0 - 100.0 | Available in Framingham | Direct numeric |
| `sex` | `float` | 0.0 = Female, 1.0 = Male | 0.0 or 1.0 | Available in Framingham | Direct binary |
| `bmi` | `float` | kg/m² | 10.0 - 80.0 | Available in Framingham | Median imputation if missing (25.4) |
| `systolic_bp_mmHg` | `float` | mmHg | 70.0 - 250.0 | Available in Framingham | Direct numeric |
| `diastolic_bp_mmHg` | `float` | mmHg | 40.0 - 150.0 | Available in Framingham | Direct numeric |
| `heart_rate` | `float` | bpm | 40.0 - 220.0 | Available in Framingham | Direct numeric |
| `cholesterol` | `float` | mg/dL | 50.0 - 600.0 | Available in Framingham | Median imputation if missing (234.0) |
| `glucose` | `float` | mg/dL | 40.0 - 400.0 | Available in Framingham | Median imputation if missing (78.0) |
| `smoking_status` | `float` | 0.0 = Non-smoker, 1.0 = Smoker | 0.0 or 1.0 | Available in Framingham | Direct binary |
| `physical_activity` | `float` | 0.0 = Inactive, 1.0 = Active | 0.0 or 1.0 | Unavailable in Framingham | Imputed with training median/mode (0.0) |
| `stress_level` | `float` | 0.0 = Low, 1.0 = Moderate/High | 0.0 or 1.0 | Unavailable in Framingham | Imputed with training median/mode (0.0) |

## 3. Provenance & Rejection Notice
The 175k Kaggle synthetic dataset was investigated and rejected because its target labels were uncoupled from blood pressure and physiological variables. The model was trained and calibrated exclusively on the real clinical Framingham cohort.
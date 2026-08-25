# HEART_MODEL_FEATURE_CONTRACT

This document specifies the exact feature contract for the LifeOS Heart Disease risk prediction model.

## Required Feature Columns (12 Total)

| Feature | Type | Expected Range | Allowed Values | Required | Handling / Notes |
| --- | --- | --- | --- | --- | --- |
| age_years | float | 18.0 - 100.0 | Continuous age in years | Yes | Numeric age in years. |
| sex | float | 0.0 or 1.0 | 0 = Female, 1 = Male | Yes | Coded binary sex indicator. |
| height_cm | float | 100.0 - 220.0 | Continuous height in cm | No | Used with weight_kg to derive BMI if missing. |
| weight_kg | float | 30.0 - 250.0 | Continuous weight in kg | No | Used with height_cm to derive BMI if missing. |
| bmi | float | 10.0 - 80.0 | Continuous BMI (kg/m²) | No | Derived as weight_kg / (height_cm / 100)² if missing. |
| systolic_bp_mmHg | int | 70 - 250 | Continuous Systolic BP | Yes | Systolic blood pressure in mmHg. |
| diastolic_bp_mmHg | float | 40.0 - 150.0 | Continuous Diastolic BP | No | Median imputed if omitted. |
| smoking_status | float | 0.0 or 1.0 | 0 = Non-smoker, 1 = Smoker | No | Most-frequent imputed if omitted. |
| alcohol_status | float | 0.0 or 1.0 | 0 = Non-drinker, 1 = Drinker | No | Most-frequent imputed if omitted. |
| physical_activity | float | 0.0 or 1.0 | 0 = Inactive, 1 = Active | No | Most-frequent imputed if omitted. |
| cholesterol_ordinal | float | 1.0, 2.0, 3.0 | 1 = Normal, 2 = Above Normal, 3 = High | No | Most-frequent imputed if omitted. |
| glucose_ordinal | float | 1.0, 2.0, 3.0 | 1 = Normal, 2 = Above Normal, 3 = High | No | Most-frequent imputed if omitted. |

## Coding Rules
- `sex`: `0.0` = Female, `1.0` = Male.
- `cholesterol_ordinal`: `1.0` = Normal (<200 mg/dL), `2.0` = Above Normal (200-239 mg/dL), `3.0` = Well Above Normal (>=240 mg/dL).
- `glucose_ordinal`: `1.0` = Normal (<100 mg/dL), `2.0` = Above Normal (100-125 mg/dL), `3.0` = Well Above Normal (>=126 mg/dL).
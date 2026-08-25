# OBESITY MODEL FEATURE CONTRACT

This document specifies the authoritative input feature contract for the LifeOS Obesity LightGBM Model.

## 1. Model Identity
- **Disease**: Obesity Risk (Behavioral / Lifestyle Risk Estimator)
- **Model Type**: LightGBM Classifier (Sigmoid / Platt Scaled)
- **Model Version**: `1.0.0`
- **Operating Threshold**: `0.50`
- **Primary Training Source**: Benchmark UCI Obesity & Eating Habits Dataset (2,087 deduplicated records)

## 2. Input Features Specification (14 Features)

| Feature Name | Data Type | Units / Encoding | Valid Range | Preprocessing Strategy |
| --- | --- | --- | --- | --- |
| `age_years` | `float` | Years | 14.0 - 100.0 | Direct numeric |
| `sex` | `float` | 0.0 = Female, 1.0 = Male | 0.0 or 1.0 | Direct binary |
| `family_history_obesity` | `float` | 0.0 = No, 1.0 = Yes | 0.0 or 1.0 | Direct binary |
| `frequent_high_calorie_food` | `float` | 0.0 = No, 1.0 = Yes | 0.0 or 1.0 | Direct binary |
| `vegetable_consumption` | `float` | Scale 1.0 (Low) - 3.0 (High) | 1.0 - 3.0 | Direct float |
| `meals_per_day` | `float` | Scale 1.0 - 4.0 meals | 1.0 - 4.0 | Direct float |
| `between_meal_eating` | `float` | 0=No, 1=Sometimes, 2=Freq, 3=Always | 0.0 - 3.0 | Ordinal float |
| `smoking_status` | `float` | 0.0 = No, 1.0 = Yes | 0.0 or 1.0 | Direct binary |
| `water_intake_l` | `float` | Daily Liters (1.0 - 3.0) | 1.0 - 3.0 | Direct float |
| `calorie_monitoring` | `float` | 0.0 = No, 1.0 = Yes | 0.0 or 1.0 | Direct binary |
| `physical_activity_frequency` | `float` | Days / week (0.0 - 3.0) | 0.0 - 3.0 | Direct float |
| `technology_usage_hours` | `float` | Hours / day (0.0 - 2.0) | 0.0 - 2.0 | Direct float |
| `alcohol_use` | `float` | 0=No, 1=Sometimes, 2=Freq, 3=Always | 0.0 - 3.0 | Ordinal float |
| `transportation_mode` | `float` | 0.0 = Active, 1.0 = Sedentary | 0.0 or 1.0 | Direct binary |

## 3. Explicit Target Leakage Exclusion Notice
To prevent trivial target leakage during lifestyle risk estimation, `Height`, `Weight`, `BMI`, and `NObeyesdad` are **100% EXCLUDED** from the model feature matrix. The model strictly estimates non-trivial behavioral and lifestyle risk.
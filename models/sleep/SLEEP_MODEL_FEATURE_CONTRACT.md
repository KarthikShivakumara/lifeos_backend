# SLEEP INTELLIGENCE MODEL FEATURE CONTRACT

---

## 1. Feature Input Specifications

| Feature Name | Type | Datatype | Range / Valid Values | Preprocessing Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| `Gender` | Categorical | String | `Male`, `Female` | OneHotEncoder |
| `Age` | Numerical | Float | 27.0 – 59.0 years | Median Imputer + StandardScaler |
| `Occupation` | Categorical | String | 11 professional roles | OneHotEncoder |
| `Sleep Duration` | Numerical | Float | 5.8 – 8.5 hours | Median Imputer + StandardScaler |
| `Quality of Sleep` | Numerical | Float | 4.0 – 9.0 (Scale) | Median Imputer + StandardScaler |
| `Physical Activity Level` | Numerical | Float | 30.0 – 90.0 minutes | Median Imputer + StandardScaler |
| `Stress Level` | Numerical | Float | 3.0 – 8.0 (Scale) | Median Imputer + StandardScaler |
| `BMI Category` | Categorical | String | `Normal`, `Overweight`, `Obese` | OneHotEncoder |
| `systolic_bp` | Numerical | Float | 90.0 – 180.0 mmHg | Median Imputer + StandardScaler |
| `diastolic_bp` | Numerical | Float | 60.0 – 120.0 mmHg | Median Imputer + StandardScaler |
| `Heart Rate` | Numerical | Float | 65.0 – 86.0 bpm | Median Imputer + StandardScaler |
| `Daily Steps` | Numerical | Float | 3,000 – 10,000 steps | Median Imputer + StandardScaler |

---

## 2. Inferred Target & Invariants
- Target Label: `target` (0 = Healthy / Low Sleep Risk, 1 = Elevated Sleep Disorder Risk).
- Excluded Column: `Person ID` 100% excluded to prevent row ID memorization.
- Architectural Boundary: Belongs to **Layer B — Wellness Intelligence**. Excluded from Layer A Disease Risk Fusion.

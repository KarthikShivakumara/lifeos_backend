# CHRONIC KIDNEY DISEASE (CKD) MODEL FEATURE CONTRACT

---

## 1. Feature Specification Table

| Feature Name | Type | Datatype | Valid Range / Options | Imputation |
| :--- | :--- | :--- | :--- | :--- |
| `age` | Numerical | Float | 1.0 – 120.0 years | Median |
| `bp` | Numerical | Float | 40.0 – 200.0 mmHg | Median |
| `sg` | Numerical | Float | 1.005 – 1.030 | Median |
| `al` | Numerical | Float | 0.0 – 5.0 | Median |
| `su` | Numerical | Float | 0.0 – 5.0 | Median |
| `bgr` | Numerical | Float | 40.0 – 500.0 mg/dL | Median |
| `bu` | Numerical | Float | 5.0 – 400.0 mg/dL | Median |
| `sc` | Numerical | Float | 0.1 – 20.0 mg/dL | Median |
| `sod` | Numerical | Float | 100.0 – 180.0 mEq/L | Median |
| `pot` | Numerical | Float | 2.0 – 10.0 mEq/L | Median |
| `hemo` | Numerical | Float | 3.0 – 20.0 g | Median |
| `pcv` | Numerical | Float | 10.0 – 60.0 % | Median |
| `wc` | Numerical | Float | 2,000 – 30,000 /cumm | Median |
| `rc` | Numerical | Float | 1.0 – 10.0 /cmm | Median |
| `rbc` | Categorical | String | `normal`, `abnormal` | Mode |
| `pc` | Categorical | String | `normal`, `abnormal` | Mode |
| `pcc` | Categorical | String | `present`, `notpresent` | Mode |
| `ba` | Categorical | String | `present`, `notpresent` | Mode |
| `htn` | Categorical | String | `yes`, `no` | Mode |
| `dm` | Categorical | String | `yes`, `no` | Mode |
| `cad` | Categorical | String | `yes`, `no` | Mode |
| `appet` | Categorical | String | `good`, `poor` | Mode |
| `pe` | Categorical | String | `yes`, `no` | Mode |
| `ane` | Categorical | String | `yes`, `no` | Mode |

---

## 2. Inferences & Target Handling
- Target: `classification` (0 = notckd, 1 = ckd).
- Identifiers: `id` column 100% excluded.

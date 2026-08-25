# STROKE MODEL FEATURE CONTRACT

---

## 1. Feature Contract Definition

This feature contract defines the exact input vector order, datatypes, valid ranges, categorical choices, and missing value imputation rules for the LifeOS Stroke Disease Risk Model (`stroke_final.pkl`).

---

## 2. Input Feature Specification

| Feature Name | Datatype | Type | Valid Range / Categories | Imputation Strategy | Semantic Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `gender` | String | Categorical | `Male`, `Female` | Most Frequent | Patient biological sex |
| `age` | Float | Numerical | 0.0 – 120.0 | Median | Patient age in years |
| `hypertension` | Integer | Binary | `0` (No), `1` (Yes) | Median | Diagnosed hypertension history |
| `heart_disease` | Integer | Binary | `0` (No), `1` (Yes) | Median | Diagnosed heart disease history |
| `ever_married` | String | Categorical | `No`, `Yes` | Most Frequent | Marital history status |
| `work_type` | String | Categorical | `Private`, `Self-employed`, `Govt_job`, `children`, `Never_worked` | Most Frequent | Employment classification |
| `Residence_type` | String | Categorical | `Urban`, `Rural` | Most Frequent | Residential environment |
| `avg_glucose_level` | Float | Numerical | 40.0 – 300.0 mg/dL | Median | Average blood glucose level |
| `bmi` | Float | Numerical | 10.0 – 70.0 kg/m² | Median | Body Mass Index |
| `smoking_status` | String | Categorical | `formerly smoked`, `never smoked`, `smokes`, `Unknown` | Most Frequent | Smoking history status |

---

## 3. Target Exclusion & Leakage Audit

- **`id`**: Excluded from training matrix to prevent arbitrary row ID memorization.
- **`stroke`**: Target label (0 = No stroke, 1 = Stroke). Excluded from feature inputs.

---

## 4. Deterministic Preprocessing Pipeline
- **Numerical Scaling**: Fitted `StandardScaler` on training set.
- **Categorical Encoding**: One-Hot Encoded with `sparse_output=False` and `handle_unknown='ignore'`.

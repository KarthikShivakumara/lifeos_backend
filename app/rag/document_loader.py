from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HealthDocument:
    document_id: str
    title: str
    source: str
    source_url: str
    topic: str
    version: str
    retrieved_at: str
    content: str


TRUSTED_HEALTH_DOCUMENTS: list[HealthDocument] = [
    HealthDocument(
        document_id="doc-hypertension-01",
        title="ACC/AHA Clinical Practice Guidelines for High Blood Pressure",
        source="American College of Cardiology / American Heart Association",
        source_url="https://www.acc.org/guidelines/hypertension",
        topic="hypertension",
        version="2023.1",
        retrieved_at="2026-01-15T00:00:00Z",
        content=(
            "Hypertension is defined as a systolic blood pressure (SBP) of 130 mmHg or higher or a diastolic blood pressure (DBP) "
            "of 80 mmHg or higher. Stage 1 hypertension ranges from 130-139 / 80-89 mmHg, while Stage 2 ranges from 140/90 mmHg or above. "
            "Systolic blood pressure above 160 mmHg is a major independent contributor to arterial stiffness, coronary artery disease, "
            "stroke, and left ventricular hypertrophy. First-line lifestyle modifications include dietary sodium restriction (< 2,000 mg/day), "
            "regular aerobic physical activity (at least 150 minutes/week of moderate intensity), weight management, and stress reduction. "
            "Home blood pressure monitoring morning and evening provides accurate tracking of arterial pressure fluctuations."
        ),
    ),
    HealthDocument(
        document_id="doc-diabetes-01",
        title="ADA Standards of Care in Diabetes: Glycemic Targets & Risk Management",
        source="American Diabetes Association",
        source_url="https://diabetes.org/standards-of-care",
        topic="diabetes",
        version="2024.1",
        retrieved_at="2026-01-15T00:00:00Z",
        content=(
            "Diabetes mellitus risk is strongly predicted by blood glucose levels, HbA1c, age, BMI, and hypertension history. "
            "An HbA1c level of 5.7% to 6.4% indicates prediabetes, while HbA1c >= 6.5% or fasting plasma glucose >= 126 mg/dL indicates diabetes. "
            "HbA1c reflects average blood sugar levels over the preceding 2 to 3 months. Elevated HbA1c is a dominant positive contributor "
            "to microvascular and macrovascular complications. Lifestyle interventions emphasizing structured diet (low glycemic index foods, "
            "soluble dietary fiber), weight loss of 5-7%, and regular physical exercise significantly reduce progression from prediabetes to diabetes."
        ),
    ),
    HealthDocument(
        document_id="doc-heart-01",
        title="AHA/ACC Cardiovascular Disease Prevention & Risk Assessment",
        source="American Heart Association",
        source_url="https://www.heart.org/guidelines/cvd-prevention",
        topic="heart_disease",
        version="2023.2",
        retrieved_at="2026-01-15T00:00:00Z",
        content=(
            "Coronary heart disease risk factors include age, biological sex, systolic blood pressure, total cholesterol, high-density lipoprotein (HDL), "
            "fasting glucose, and tobacco smoking status. Smoking status is a potent modifiable factor introducing vascular endothelial damage, "
            "accelerating coronary plaque deposition, and elevating arterial thrombosis risk. Physical activity decreases cardiac workload and "
            "improves lipid profile (elevating HDL and lowering triglycerides). Combining dietary cholesterol control with 150+ minutes of weekly "
            "aerobic movement lowers estimated 10-year atherosclerotic cardiovascular disease (ASCVD) risk."
        ),
    ),
    HealthDocument(
        document_id="doc-obesity-01",
        title="WHO & NIH Obesity Guidelines: Behavioral & Lifestyle Risk Factors",
        source="World Health Organization / National Institutes of Health",
        source_url="https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
        topic="obesity",
        version="2023.1",
        retrieved_at="2026-01-15T00:00:00Z",
        content=(
            "Obesity is a complex multifactorial condition influenced by behavioral, dietary, physical activity, and genetic factors. "
            "Body Mass Index (BMI) >= 25 is classified as overweight, and BMI >= 30 as obesity. However, non-trivial lifestyle risk factors—such as "
            "frequent consumption of high-calorie foods, low vegetable intake, high sedentary screen time, insufficient water intake (< 2L/day), "
            "and physical inactivity—predict cardiometabolic risk independent of direct BMI algebraic formulas. Sustainable weight management relies on "
            "gradual caloric control, whole nutrient-dense foods, regular daily movement, and behavioral habit tracking."
        ),
    ),
    HealthDocument(
        document_id="doc-lifestyle-01",
        title="CDC Guidelines: Modifiable Risk Factors (Smoking, Alcohol, Sleep, Physical Activity)",
        source="Centers for Disease Control and Prevention",
        source_url="https://www.cdc.gov/chronicdisease/resources/publications/factsheets",
        topic="lifestyle",
        version="2024.1",
        retrieved_at="2026-01-15T00:00:00Z",
        content=(
            "Four core modifiable lifestyle behaviors drive over 80% of chronic cardiometabolic conditions (hypertension, type 2 diabetes, "
            "heart disease, and obesity): 1) Tobacco Cessation: Quitting smoking rapidly improves endothelial function and blood pressure within weeks; "
            "2) Physical Activity: 150-300 minutes of moderate activity weekly enhances insulin sensitivity and lowers SBP by 5-8 mmHg; "
            "3) Sleep Hygiene: 7-9 hours of nightly restorative sleep regulates cortisol, ghrelin, and glycemic control; "
            "4) Hydration & Stress Management: Adequate water intake (2-3L/day) and stress reduction optimize autonomic cardiovascular regulation."
        ),
    ),
]


class DocumentLoader:
    def load_documents(self) -> list[HealthDocument]:
        return TRUSTED_HEALTH_DOCUMENTS

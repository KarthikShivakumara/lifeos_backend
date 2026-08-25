from __future__ import annotations

import logging
import uuid
from typing import Any

from app.schemas.recommendation import (
    RecommendationEngineResponse,
    RecommendationItem,
    RecommendationPriority,
    RecommendationRequest,
)


logger = logging.getLogger("lifeos.recommendation_service")

PRIORITY_WEIGHTS: dict[RecommendationPriority, int] = {
    "urgent": 4,
    "high": 3,
    "moderate": 2,
    "low": 1,
}


class RecommendationService:
    _instance: RecommendationService | None = None

    @classmethod
    def get_instance(cls) -> RecommendationService:
        if cls._instance is None:
            cls._instance = RecommendationService()
        return cls._instance

    def _extract_shap_contributors(self, disease_result: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not disease_result:
            return []
        explanation = disease_result.get("explanation")
        if isinstance(explanation, dict):
            return explanation.get("top_contributors", [])
        if "top_contributors" in disease_result:
            return disease_result.get("top_contributors", [])
        return []

    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationEngineResponse:
        inputs = request.assessment_input or {}

        # Extract model prediction results
        heart_res = request.heart
        diabetes_res = request.diabetes
        htn_res = request.hypertension
        obesity_res = request.obesity
        fusion_res = request.risk_fusion

        # SHAP contributors
        heart_shap = self._extract_shap_contributors(heart_res)
        diabetes_shap = self._extract_shap_contributors(diabetes_res)
        htn_shap = self._extract_shap_contributors(htn_res)
        obesity_shap = self._extract_shap_contributors(obesity_res)

        generated: list[RecommendationItem] = []

        # 1. MEDICAL FOLLOW UP & URGENT EVALUATION RULE
        overall_risk_level = fusion_res.get("overall_risk_level") if fusion_res else None
        multiple_high = fusion_res.get("multiple_high_risk") if fusion_res else False
        top_priority_disease = fusion_res.get("top_priority_display_name", "Cardiometabolic") if fusion_res else "Cardiometabolic"

        if overall_risk_level == "very_high" or multiple_high:
            generated.append(
                RecommendationItem(
                    id=f"rec-med-{uuid.uuid4().hex[:8]}",
                    category="medical_follow_up",
                    priority="urgent",
                    title="Schedule Professional Health Consultation",
                    description=f"Your submitted health markers indicate multi-system risk, with {top_priority_disease} identified as the highest priority.",
                    reason=f"The LifeOS Risk Fusion Engine detected elevated risk scores across multiple disease models ({top_priority_disease} model risk: {fusion_res.get('top_priority_score', 0)*100:.1f}%).",
                    related_diseases=[d for d in ["heart", "diabetes", "hypertension", "obesity"] if (request.__getattribute__(d) or {}).get("risk_score", 0) >= 0.50],
                    source_feature="risk_fusion_engine",
                    action="Schedule a comprehensive clinical assessment with a primary care physician to evaluate blood pressure, lipid panel, and glycemic markers.",
                )
            )

        # 2. BLOOD PRESSURE RULE
        sys_bp = float(inputs.get("systolic_bp", inputs.get("systolic_bp_mmHg", 0)))
        dia_bp = float(inputs.get("diastolic_bp", inputs.get("diastolic_bp_mmHg", 0)))
        htn_risk = float((htn_res or {}).get("risk_score", 0))

        if sys_bp >= 140 or dia_bp >= 90 or htn_risk >= 0.60:
            bp_priority: RecommendationPriority = "urgent" if (sys_bp >= 160 or dia_bp >= 100) else "high"

            # Check SHAP for BP contribution
            bp_shap_match = next((item for item in htn_shap if "bp" in item.get("feature", "").lower() or "systolic" in item.get("feature", "").lower()), None)
            reason_txt = (
                f"Systolic/Diastolic blood pressure contributed strongly (+{bp_shap_match['contribution']:.4f}) to the Hypertension model risk estimate."
                if bp_shap_match
                else f"Submitted BP readings ({int(sys_bp)}/{int(dia_bp)} mmHg) and Hypertension model risk score ({htn_risk*100:.1f}%) indicate elevated vascular strain."
            )

            generated.append(
                RecommendationItem(
                    id=f"rec-bp-{uuid.uuid4().hex[:8]}",
                    category="blood_pressure",
                    priority=bp_priority,
                    title="Monitor & Manage Blood Pressure",
                    description="Elevated arterial pressure increases cardiac workload and vascular resistance.",
                    reason=reason_txt,
                    related_diseases=["hypertension", "heart"],
                    source_feature="systolic_bp_mmHg",
                    action="Log daily home blood pressure readings morning and evening. Limit dietary sodium intake to under 2,000 mg/day.",
                )
            )

        # 3. BLOOD GLUCOSE & HBA1C RULE
        glucose = float(inputs.get("glucose", inputs.get("blood_glucose_level", 0)))
        hba1c = float(inputs.get("hba1c", inputs.get("hba1c_level", 0)))
        diab_risk = float((diabetes_res or {}).get("risk_score", 0))

        if glucose >= 126 or hba1c >= 6.5 or diab_risk >= 0.70:
            gl_priority: RecommendationPriority = "urgent" if (glucose >= 180 or hba1c >= 8.0) else "high"

            hba1c_shap = next((item for item in diabetes_shap if "hba1c" in item.get("feature", "").lower()), None)
            reason_txt = (
                f"HbA1c was a dominant contributor (+{hba1c_shap['contribution']:.4f}) to the Diabetes model risk score."
                if hba1c_shap
                else f"Glycemic indicators (Glucose: {glucose} mg/dL, HbA1c: {hba1c}%) and Diabetes model risk ({diab_risk*100:.1f}%) warrant proactive management."
            )

            generated.append(
                RecommendationItem(
                    id=f"rec-glucose-{uuid.uuid4().hex[:8]}",
                    category="blood_glucose",
                    priority=gl_priority,
                    title="Glycemic Control & Carbohydrate Management",
                    description="Consistent blood sugar monitoring helps prevent glycemic spikes and metabolic stress.",
                    reason=reason_txt,
                    related_diseases=["diabetes"],
                    source_feature="hba1c_level" if hba1c_shap else "blood_glucose_level",
                    action="Prioritize low-glycemic foods, increase dietary soluble fiber, and consult a doctor for formal HbA1c laboratory testing.",
                )
            )

        # 4. WEIGHT MANAGEMENT RULE
        bmi = float(inputs.get("bmi", 0))
        weight_kg = float(inputs.get("weight_kg", 0))
        height_cm = float(inputs.get("height_cm", 0))
        if bmi == 0 and weight_kg > 0 and height_cm > 0:
            bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 2)

        obes_risk = float((obesity_res or {}).get("risk_score", 0))

        if bmi >= 25.0 or obes_risk >= 0.50:
            wm_priority: RecommendationPriority = "high" if (bmi >= 30.0 or obes_risk >= 0.75) else "moderate"

            fam_shap = next((item for item in obesity_shap if "family" in item.get("feature", "").lower() or "calorie" in item.get("feature", "").lower()), None)
            reason_txt = (
                f"Behavioral lifestyle patterns ({fam_shap['human_readable']}) and Obesity model risk ({obes_risk*100:.1f}%) highlight opportunities for metabolic optimization."
                if fam_shap
                else f"Body Mass Index ({bmi:.1f} kg/m²) and lifestyle obesity risk score ({obes_risk*100:.1f}%) indicate benefit from energy balance adjustment."
            )

            generated.append(
                RecommendationItem(
                    id=f"rec-weight-{uuid.uuid4().hex[:8]}",
                    category="weight_management",
                    priority=wm_priority,
                    title="Sustainable Weight & Lifestyle Management",
                    description="Gradual, sustainable body composition management improves overall insulin sensitivity and cardiovascular strain.",
                    reason=reason_txt,
                    related_diseases=["obesity", "diabetes", "heart"],
                    source_feature="bmi" if bmi > 0 else "family_history_obesity",
                    action="Focus on nutrient-dense whole foods, mindful portion management, and regular daily physical movement.",
                )
            )

        # 5. PHYSICAL ACTIVITY RULE (DEDUPLICATED MULTI-DISEASE REASONING)
        exercise_str = str(inputs.get("exercise_frequency", inputs.get("physical_activity", ""))).lower()
        heart_risk = float((heart_res or {}).get("risk_score", 0))

        is_inactive = exercise_str in ["none", "inactive", "0", "0.0"]
        if is_inactive or heart_risk >= 0.40 or htn_risk >= 0.60 or obes_risk >= 0.50:
            act_diseases = []
            if heart_risk >= 0.40:
                act_diseases.append("heart")
            if htn_risk >= 0.60:
                act_diseases.append("hypertension")
            if obes_risk >= 0.50:
                act_diseases.append("obesity")

            generated.append(
                RecommendationItem(
                    id=f"rec-act-{uuid.uuid4().hex[:8]}",
                    category="physical_activity",
                    priority="high" if is_inactive else "moderate",
                    title="Increase Regular Aerobic Physical Activity",
                    description="Consistent physical exercise enhances endothelial function, lowers resting blood pressure, and improves lipid metabolism.",
                    reason=f"Exercise habits were flagged as an actionable variable for multiple disease verticals ({', '.join(act_diseases) if act_diseases else 'preventive baseline'}).",
                    related_diseases=act_diseases or ["heart", "hypertension", "obesity"],
                    source_feature="exercise_frequency",
                    action="Aim for 150 minutes of moderate-intensity aerobic exercise (such as brisk walking, cycling, or swimming) per week.",
                )
            )

        # 6. SMOKING CESSATION RULE
        smoking_str = str(inputs.get("smoking_status", "")).lower()
        if smoking_str in ["smoker", "yes", "1", "1.0"]:
            generated.append(
                RecommendationItem(
                    id=f"rec-smoke-{uuid.uuid4().hex[:8]}",
                    category="smoking",
                    priority="urgent",
                    title="Pursue Structured Smoking Cessation Support",
                    description="Tobacco smoke introduces systemic endothelial damage, accelerates coronary plaque formation, and elevates arterial stiffness.",
                    reason="Smoking status was identified as a major modifiable risk factor elevating risk across Heart, Hypertension, and Diabetes models.",
                    related_diseases=["heart", "hypertension", "diabetes"],
                    source_feature="smoking_status",
                    action="Explore evidence-based smoking cessation resources, nicotine replacement therapy, or behavioral counseling with your healthcare provider.",
                )
            )

        # 7. ALCOHOL MODERATION RULE
        alc_str = str(inputs.get("alcohol_use", inputs.get("alcohol_status", ""))).lower()
        if alc_str in ["yes", "drinker", "1", "1.0", "frequently", "sometimes"]:
            generated.append(
                RecommendationItem(
                    id=f"rec-alc-{uuid.uuid4().hex[:8]}",
                    category="alcohol",
                    priority="moderate",
                    title="Moderate Alcohol Consumption",
                    description="Excessive alcohol intake can elevate blood pressure, increase hepatic fat accumulation, and contribute surplus calories.",
                    reason="Submitted alcohol usage indicated regular intake, which influences cardiovascular and obesity risk profiles.",
                    related_diseases=["hypertension", "obesity", "heart"],
                    source_feature="alcohol_use",
                    action="Limit alcohol consumption to no more than 1 standard drink per day for women or 2 for men, and incorporate alcohol-free days.",
                )
            )

        # 8. SLEEP HYGIENE RULE
        sleep_hours = float(inputs.get("sleep_hours", 7.0))
        if sleep_hours < 7.0:
            generated.append(
                RecommendationItem(
                    id=f"rec-sleep-{uuid.uuid4().hex[:8]}",
                    category="sleep",
                    priority="moderate",
                    title="Optimize Sleep Duration & Hygiene",
                    description="Insufficient sleep (< 7 hours/night) disrupts nocturnal blood pressure dipping and elevates morning cortisol levels.",
                    reason=f"Reported sleep duration ({sleep_hours} hours/night) falls below the recommended 7-9 hour circadian recovery window.",
                    related_diseases=["hypertension", "heart", "obesity"],
                    source_feature="sleep_hours",
                    action="Maintain a consistent bedtime schedule, eliminate ambient light and screens 1 hour before sleep, and target 7 to 8 hours nightly.",
                )
            )

        # 9. HYDRATION RULE
        water_l = float(inputs.get("water_intake_l", 2.0))
        if water_l < 2.0:
            generated.append(
                RecommendationItem(
                    id=f"rec-hyd-{uuid.uuid4().hex[:8]}",
                    category="hydration",
                    priority="low",
                    title="Enhance Daily Fluid & Water Intake",
                    description="Adequate hydration supports renal filtration, vascular volume regulation, and digestive health.",
                    reason=f"Daily water intake ({water_l} L/day) is below recommended metabolic baseline targets.",
                    related_diseases=["obesity", "hypertension"],
                    source_feature="water_intake_l",
                    action="Increase plain water consumption to at least 2.0 to 2.5 liters daily.",
                )
            )

        # 10. STRESS MANAGEMENT RULE
        stress_str = str(inputs.get("stress_level", "")).lower()
        dep_score = float(inputs.get("depression_score", 0))
        if stress_str in ["high", "very_high", "elevated"] or dep_score >= 50:
            generated.append(
                RecommendationItem(
                    id=f"rec-stress-{uuid.uuid4().hex[:8]}",
                    category="stress_management",
                    priority="moderate",
                    title="Practice Stress Reduction & Mindful Recovery",
                    description="Chronic psychological stress drives sympathetic nervous system hyperactivity, raising heart rate and blood pressure.",
                    reason=f"Stress markers (Level: '{stress_str}', Score: {dep_score}) indicate elevated neuroendocrine strain.",
                    related_diseases=["hypertension", "heart"],
                    source_feature="stress_level",
                    action="Integrate daily mindfulness techniques, deep diaphragmatic breathing exercises, or structured stress-reduction practices.",
                )
            )

        # 11. PHYSICAL ACTIVITY WELLNESS RULE
        act_res = request.activity
        act_score = None
        act_level = None
        sed_hrs = None
        act_trend = None

        if act_res and isinstance(act_res, dict):
            act_score = act_res.get("activity_score") or act_res.get("score")
            act_level = act_res.get("activity_level") or act_res.get("level")
            meta = act_res.get("metadata", {})
            sed_hrs = meta.get("sedentary_hours")
            act_trend = meta.get("weekly_trend")

        # Also fallback to direct inputs
        if act_score is None:
            steps_val = inputs.get("daily_steps") or inputs.get("steps")
            if steps_val and float(steps_val) < 5000:
                act_level = "low"

        if act_level == "low" or (act_score is not None and float(act_score) < 40.0):
            generated.append(
                RecommendationItem(
                    id=f"rec-act-{uuid.uuid4().hex[:8]}",
                    category="physical_activity",
                    priority="high",
                    title="Gradual Daily Movement & Step Expansion",
                    description="Regular physical movement improves insulin sensitivity, endothelial function, and daily energy expenditure.",
                    reason="Recent activity indicators suggest step counts or active minutes fall below recommended wellness baselines.",
                    related_diseases=["heart", "diabetes", "obesity"],
                    source_feature="daily_steps",
                    action="Aim for a gradual increase in daily movement by taking 10-15 minute walking breaks after meals.",
                )
            )
        elif sed_hrs is not None and float(sed_hrs) >= 10.0:
            generated.append(
                RecommendationItem(
                    id=f"rec-act-sed-{uuid.uuid4().hex[:8]}",
                    category="physical_activity",
                    priority="moderate",
                    title="Introduce Periodic Sedentary Movement Breaks",
                    description="Extended uninterrupted sitting (>10 hours/day) reduces peripheral circulation and muscle glucose uptake.",
                    reason=f"Recorded daily sedentary duration ({sed_hrs} hours) exceeds optimal wellness thresholds.",
                    related_diseases=["hypertension", "diabetes"],
                    source_feature="sedentary_hours",
                    action="Set hourly reminders to stand, stretch, or walk for 2 to 3 minutes during long sedentary periods.",
                )
            )

        # 12. NUTRITION BASELINE RULE (If no specific nutrition trigger fired)
        diet_str = str(inputs.get("diet_quality", "")).lower()
        veg_cons = float(inputs.get("vegetable_consumption", 2.4))
        if diet_str in ["poor", "fast_food", "unhealthy"] or veg_cons < 2.0 or not any(r.category == "nutrition" for r in generated):
            generated.append(
                RecommendationItem(
                    id=f"rec-nutr-{uuid.uuid4().hex[:8]}",
                    category="nutrition",
                    priority="high" if diet_str in ["poor", "fast_food"] else "moderate",
                    title="Adopt Heart-Healthy Mediterranean Diet Pattern",
                    description="A diet rich in vegetables, legumes, lean proteins, and healthy fats improves lipid profiles and vascular endothelial health.",
                    reason="Dietary quality indicators point to opportunities for reducing ultra-processed food and increasing antioxidant-rich vegetables.",
                    related_diseases=["heart", "diabetes", "hypertension", "obesity"],
                    source_feature="diet_quality",
                    action="Increase daily intake of leafy vegetables, berries, nuts, and olive oil while reducing refined carbohydrates and trans fats.",
                )
            )

        # Sort recommendations by Priority (urgent -> high -> moderate -> low)
        sorted_recs = sorted(generated, key=lambda x: PRIORITY_WEIGHTS.get(x.priority, 1), reverse=True)

        return RecommendationEngineResponse(
            recommendations=sorted_recs,
            top_recommendations=sorted_recs[:5],
            total_count=len(sorted_recs),
            generated_from={
                "heart": heart_res is not None,
                "diabetes": diabetes_res is not None,
                "hypertension": htn_res is not None,
                "obesity": obesity_res is not None,
                "risk_fusion": fusion_res is not None,
            },
        )


recommendation_service = RecommendationService.get_instance()

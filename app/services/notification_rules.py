from __future__ import annotations

from typing import Any


class NotificationRuleEngine:
    def evaluate_overall_risk_rule(self, risk_fusion: dict[str, Any]) -> dict[str, Any] | None:
        ov_score = risk_fusion.get("overall_risk_score")
        ov_pct = risk_fusion.get("overall_risk_percentage")
        if ov_pct is None and ov_score is not None:
            ov_pct = float(ov_score) * 100.0

        if ov_pct is None or ov_pct < 70.0:
            return None

        priority = "urgent" if ov_pct >= 80.0 else "high"
        title = "Very High Overall Health Risk Detected" if ov_pct >= 80.0 else "High Overall Health Risk Detected"
        msg = (
            f"Your latest LifeOS assessment indicates an overall health risk score of {ov_pct:.1f}%. "
            f"Please review your screening results and consider discussing concerning findings with a qualified healthcare professional."
        )

        return {
            "type": "high_risk_alert",
            "title": title,
            "message": msg,
            "priority": priority,
            "action_url": "/dashboard",
            "metadata": {"overall_risk_percentage": ov_pct},
        }

    def evaluate_disease_rules(self, disease_results: dict[str, Any]) -> dict[str, Any] | None:
        thresholds = {"heart": 0.40, "diabetes": 0.70, "hypertension": 0.60, "obesity": 0.50}
        display_names = {"heart": "Heart Disease", "diabetes": "Diabetes", "hypertension": "Hypertension", "obesity": "Obesity"}

        high_diseases: list[tuple[str, float]] = []

        for k, th in thresholds.items():
            res = disease_results.get(k)
            if res and isinstance(res, dict):
                score = res.get("risk_score")
                if score is not None and float(score) >= th:
                    high_diseases.append((display_names[k], float(score) * 100.0))

        if not high_diseases:
            return None

        if len(high_diseases) > 1:
            names_str = ", ".join([d[0] for d in high_diseases])
            return {
                "type": "high_risk_alert",
                "title": "Multiple Elevated Health Risks Detected",
                "message": f"Your latest screening indicates elevated risk estimates across multiple areas ({names_str}). Review details on your dashboard.",
                "priority": "high",
                "action_url": "/dashboard",
                "metadata": {"affected_diseases": [d[0] for d in high_diseases]},
            }
        else:
            d_name, score_pct = high_diseases[0]
            return {
                "type": "high_risk_alert",
                "title": f"Elevated {d_name} Risk Score",
                "message": f"Your latest assessment indicates an elevated {d_name} screening score of {score_pct:.1f}%. Review your recommendations.",
                "priority": "high",
                "action_url": "/dashboard",
                "metadata": {"disease": d_name, "risk_score": score_pct},
            }

    def evaluate_biomarker_rules(self, assessment_input: dict[str, Any]) -> dict[str, Any] | None:
        sbp = assessment_input.get("systolic_bp") or assessment_input.get("systolic_bp_mmHg")
        glucose = assessment_input.get("glucose") or assessment_input.get("blood_glucose_level")
        hba1c = assessment_input.get("hba1c") or assessment_input.get("hba1c_level")

        issues = []
        if sbp and float(sbp) >= 140:
            issues.append("elevated blood pressure")
        if glucose and float(glucose) >= 126:
            issues.append("elevated blood glucose")
        if hba1c and float(hba1c) >= 6.5:
            issues.append("elevated HbA1c")

        if not issues:
            return None

        return {
            "type": "high_risk_alert",
            "title": "Biomarkers Need Attention",
            "message": f"Your latest assessment contains {', '.join(issues)}. Review your recommendations and consider professional follow-up.",
            "priority": "high",
            "action_url": "/dashboard",
            "metadata": {"issues": issues},
        }

    def evaluate_recommendation_rule(self, recommendations: list[dict[str, Any]]) -> dict[str, Any] | None:
        urgent_items = [r for r in recommendations if isinstance(r, dict) and r.get("priority") in ["urgent", "high"]]
        if not urgent_items:
            return None

        return {
            "type": "recommendation_reminder",
            "title": "Follow Up on Your Health Recommendations",
            "message": f"You have {len(urgent_items)} priority health actions from your latest assessment. Review them to continue tracking your progress.",
            "priority": "moderate",
            "action_url": "/dashboard",
            "metadata": {"urgent_count": len(urgent_items)},
        }

    def evaluate_trend_rule(self, trends: Any) -> dict[str, Any] | None:
        if not trends or not hasattr(trends, "risk_trends"):
            return None
        ov_t = trends.risk_trends.overall
        if ov_t.direction == "increasing":
            return {
                "type": "trend_alert",
                "title": "Health Risk Trend Changed",
                "message": "Your latest assessment shows an increase in your overall LifeOS risk score compared with your previous assessment. Review the trend details.",
                "priority": "high",
                "action_url": "/history",
                "metadata": {"direction": "increasing", "change": ov_t.absolute_change},
            }
        elif ov_t.direction == "decreasing":
            return {
                "type": "trend_alert",
                "title": "Positive Health Trend Detected",
                "message": "Your latest assessment shows a meaningful reduction in your overall LifeOS risk score compared with your previous assessment.",
                "priority": "low",
                "action_url": "/history",
                "metadata": {"direction": "decreasing", "change": ov_t.absolute_change},
            }
        return None

    def evaluate_wellness_rules(self, disease_results: dict[str, Any]) -> dict[str, Any] | None:
        sleep_res = disease_results.get("sleep") or disease_results.get("sleep_wellness")
        if sleep_res and isinstance(sleep_res, dict):
            score = sleep_res.get("risk_score")
            th = sleep_res.get("threshold", 0.65)
            if score is not None and float(score) >= float(th):
                return {
                    "type": "wellness_checkin",
                    "title": "Sleep Wellness Attention Recommended",
                    "message": f"Your latest sleep wellness risk index ({float(score)*100:.1f}%) indicates elevated sleep disturbance patterns. Consider reviewing bedtime routine suggestions.",
                    "priority": "moderate",
                    "action_url": "/dashboard",
                    "metadata": {"domain": "sleep", "score": float(score)},
                }

        act_res = disease_results.get("activity") or disease_results.get("activity_wellness")
        if act_res and isinstance(act_res, dict):
            act_score = act_res.get("activity_score") or act_res.get("score")
            act_lvl = act_res.get("activity_level") or act_res.get("level")
            meta = act_res.get("metadata", {})
            sed_hrs = meta.get("sedentary_hours", 0.0)

            if act_lvl == "low" or (act_score is not None and float(act_score) < 40.0) or sed_hrs >= 10.0:
                return {
                    "type": "wellness_checkin",
                    "title": "Activity & Sedentary Wellness Attention",
                    "message": "Your latest activity indicators show low daily movement or elevated sedentary time. Consider scheduling short walking breaks.",
                    "priority": "moderate",
                    "action_url": "/dashboard",
                    "metadata": {"domain": "activity", "score": act_score, "level": act_lvl},
                }
        return None


rule_engine = NotificationRuleEngine()

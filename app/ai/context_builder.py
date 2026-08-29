from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.health_snapshot import HealthSnapshotModel
from app.services.history_service import history_service


@dataclass
class UserHealthContext:
    user_id: str
    has_assessment: bool
    overall_health_score: int | None
    overall_risk_percentage: float | None
    overall_risk_level: str | None
    top_priority_disease: str | None
    disease_risks: dict[str, float]
    top_shap_contributors: dict[str, list[dict[str, Any]]]
    recommendations_summary: list[str]
    trend_summary: str | None
    formatted_context_str: str


class ContextBuilder:
    def build_user_context(self, user_id: str, db: Session | None = None) -> UserHealthContext:
        snaps = history_service.get_history(user_id=user_id, db=db).snapshots
        if not snaps:
            return UserHealthContext(
                user_id=user_id,
                has_assessment=False,
                overall_health_score=None,
                overall_risk_percentage=None,
                overall_risk_level=None,
                top_priority_disease=None,
                disease_risks={},
                top_shap_contributors={},
                recommendations_summary=[],
                trend_summary=None,
                formatted_context_str="No completed health assessment recorded for this user yet.",
            )

        latest_snap = snaps[0]
        rf = latest_snap.risk_fusion or {}
        dis = latest_snap.disease_results or {}
        recs = latest_snap.recommendations or []

        ov_health = rf.get("overall_health_score")
        ov_pct = rf.get("overall_risk_percentage")
        ov_level = rf.get("overall_risk_level")
        top_priority = rf.get("top_priority_display_name")

        disease_risks: dict[str, float] = {}
        top_shaps: dict[str, list[dict[str, Any]]] = {}

        for k, name in [
            ("heart", "Heart Disease"),
            ("diabetes", "Diabetes"),
            ("hypertension", "Hypertension"),
            ("obesity", "Obesity"),
            ("stroke", "Stroke Risk"),
            ("ckd", "Chronic Kidney Disease"),
        ]:
            d_res = dis.get(k)
            if d_res:
                pred = d_res.get("prediction") if isinstance(d_res, dict) else None
                score = d_res.get("risk_score") if isinstance(d_res, dict) else (pred.get("risk_score") if isinstance(pred, dict) else None)
                if score is not None:
                    disease_risks[name] = float(score) * 100.0

                explain = d_res.get("explanation") if isinstance(d_res, dict) else None
                top_c = explain.get("top_contributors") if isinstance(explain, dict) else None
                if top_c:
                    top_shaps[name] = top_c[:3]

        rec_titles = [r.get("title") for r in recs if isinstance(r, dict) and r.get("title")]

        # Bounded trend summary if multiple snapshots exist
        trend_str = None
        if len(snaps) >= 2:
            trends = history_service.calculate_trends(snaps)
            ov_t = trends.risk_trends.overall
            trend_str = f"Overall Risk change from previous assessment: {ov_t.previous_value*100:.1f}% -> {ov_t.current_value*100:.1f}% ({ov_t.direction.upper()})."

        # Format clean bounded context block
        lines = [
            f"=== USER HEALTH CONTEXT (User ID: {user_id[:8]}) ===",
            f"Assessment Timestamp: {latest_snap.timestamp}",
        ]
        if ov_pct is not None:
            lines.append(f"Overall Risk Percentage: {ov_pct:.1f}% ({ov_level.upper() if ov_level else 'N/A'})")
            lines.append(f"Overall Health Score: {ov_health} / 100")
            lines.append(f"Top Priority Risk Area: {top_priority}")

        if disease_risks:
            lines.append("Disease Risk Model Estimates:")
            for dis_name, r_val in disease_risks.items():
                lines.append(f"  - {dis_name}: {r_val:.1f}%")

        if top_shaps:
            lines.append("Key Model Risk Contributors (TreeSHAP):")
            for dis_name, sh_list in top_shaps.items():
                sh_texts = [f"{item.get('human_readable')} ({item.get('contribution'):+.3f})" for item in sh_list if item.get('human_readable')]
                if sh_texts:
                    lines.append(f"  - {dis_name}: {', '.join(sh_texts)}")

        # Layer B Wellness Context (Sleep & Activity)
        sleep_res = dis.get("sleep") or dis.get("sleep_wellness")
        if sleep_res and isinstance(sleep_res, dict):
            s_score = sleep_res.get("risk_score")
            s_lvl = sleep_res.get("risk_level", "N/A")
            if s_score is not None:
                lines.append(f"Layer B Wellness Context - Sleep Risk Index: {float(s_score)*100:.1f}% ({str(s_lvl).upper()}) [Non-diagnostic wellness indicator]")

        act_res = dis.get("activity") or dis.get("activity_wellness")
        if act_res and isinstance(act_res, dict):
            act_score = act_res.get("activity_score") or act_res.get("score")
            act_lvl = act_res.get("activity_level") or act_res.get("level", "N/A")
            meta = act_res.get("metadata", {})
            sed_risk = meta.get("sedentary_risk", "N/A")
            act_tr = meta.get("weekly_trend", "N/A")
            if act_score is not None:
                display_score = float(act_score) * 100.0 if float(act_score) <= 1.0 else float(act_score)
                lines.append(f"Layer B Wellness Context - Physical Activity Score: {display_score:.1f}/100 (Level: {str(act_lvl).upper()}, Sedentary Risk: {str(sed_risk).upper()}, Trend: {str(act_tr).upper()}) [Non-diagnostic wellness indicator]")

        if rec_titles:
            lines.append(f"Top Active Recommendations: {', '.join(rec_titles[:4])}")

        if trend_str:
            lines.append(f"Trend Observation: {trend_str}")

        # Layer E Adaptive Personal Baselines & Longitudinal Trends
        if db is not None:
            try:
                from app.services.adaptive.baseline_service import get_user_baselines
                from app.services.adaptive.trend_service import evaluate_longitudinal_trends

                baselines = get_user_baselines(db, user_id)
                adaptive_trends = evaluate_longitudinal_trends(db, user_id)
                
                lines.append("=== LAYER E ADAPTIVE INTELLIGENCE (Personal Baselines & Trends) ===")
                for b in baselines:
                    if b.rolling_7_day_avg is not None and b.rolling_30_day_avg is not None:
                        lines.append(f"  - {b.metric.replace('_', ' ').title()}: 7d Avg = {b.rolling_7_day_avg:.1f}, 30d Avg = {b.rolling_30_day_avg:.1f} (Trend: {b.trend})")
                if adaptive_trends.get("declines"):
                    lines.append(f"  - Declining Metrics: {', '.join(adaptive_trends['declines'])}")
                if adaptive_trends.get("improvements"):
                    lines.append(f"  - Improving Metrics: {', '.join(adaptive_trends['improvements'])}")
            except Exception as err:
                pass

        formatted_str = "\n".join(lines)

        return UserHealthContext(
            user_id=user_id,
            has_assessment=True,
            overall_health_score=ov_health,
            overall_risk_percentage=ov_pct,
            overall_risk_level=ov_level,
            top_priority_disease=top_priority,
            disease_risks=disease_risks,
            top_shap_contributors=top_shaps,
            recommendations_summary=rec_titles,
            trend_summary=trend_str,
            formatted_context_str=formatted_str,
        )


context_builder = ContextBuilder()

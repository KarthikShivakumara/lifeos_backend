from __future__ import annotations

from app.schemas.stress import StressRecommendationItem


class StressRecommendationService:
    @staticmethod
    def get_recommendations(
        stress_index: float,
        stress_level: str,
        sleep_hours: float | None = None,
        activity_minutes: int | None = None,
    ) -> list[StressRecommendationItem]:
        recs: list[StressRecommendationItem] = []

        if stress_index >= 75.0 or stress_level == "high":
            recs.append(
                StressRecommendationItem(
                    title="Professional Support Reminder",
                    description=(
                        "You're reporting a high level of distress. LifeOS is a non-diagnostic wellness tool and cannot assess "
                        "clinical mental-health conditions. If you are finding stress difficult to manage, consider speaking with "
                        "a qualified healthcare or mental-health professional."
                    ),
                    priority="HIGH",
                    category="safety_escalation",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Schedule an Immediate Decompression Buffer",
                    description="Set aside a 15–20 minute quiet break away from screens, deadlines, and active demands today.",
                    priority="HIGH",
                    category="recovery",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Paced Diaphragmatic Breathing",
                    description="Practice 5 minutes of 4-7-8 breathing or box breathing to support parasympathetic autonomic recovery.",
                    priority="HIGH",
                    category="relaxation",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Connect With a Trusted Support Person",
                    description="Reach out to a family member, friend, or mentor to share your thoughts and reduce isolation.",
                    priority="MEDIUM",
                    category="social_support",
                )
            )
        elif stress_index >= 50.0 or stress_level == "moderate":
            recs.append(
                StressRecommendationItem(
                    title="Schedule a Midday Recovery Break",
                    description="Step away from work or cognitive tasks for 10 minutes to reset focus and lower tension.",
                    priority="HIGH",
                    category="recovery",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Brief Evening Relaxation Routine",
                    description="Practice progressive muscle relaxation or listen to calming audio for 10 minutes before bed.",
                    priority="MEDIUM",
                    category="relaxation",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Protect Sleep Timing",
                    description="Maintain a consistent bedtime to prevent sleep debt from compounding daytime stress.",
                    priority="MEDIUM",
                    category="sleep",
                )
            )
        elif stress_index >= 25.0 or stress_level == "mild":
            recs.append(
                StressRecommendationItem(
                    title="Maintain Balanced Daily Routines",
                    description="Your stress level is manageable. Continue your regular sleep, nutrition, and exercise routines.",
                    priority="LOW",
                    category="recovery",
                )
            )
            recs.append(
                StressRecommendationItem(
                    title="Take Micro-Breaks Between Tasks",
                    description="Take 2-minute standing and stretching breaks throughout the day to release physical tightness.",
                    priority="LOW",
                    category="relaxation",
                )
            )
        else:
            recs.append(
                StressRecommendationItem(
                    title="Optimal Stress Equilibrium",
                    description="Your reported stress is low and your coping habits are currently effective. Keep up your healthy lifestyle.",
                    priority="LOW",
                    category="recovery",
                )
            )

        # Observational lifestyle factor recommendations
        if sleep_hours is not None and sleep_hours < 6.5:
            recs.append(
                StressRecommendationItem(
                    title="Prioritize Sleep Restoration",
                    description=(
                        f"Your recorded sleep was {sleep_hours:.1f} hours. "
                        "Lower sleep duration frequently coincides with elevated perceived stress. Aim for 7–8 hours tonight."
                    ),
                    priority="HIGH" if stress_index >= 50 else "MEDIUM",
                    category="sleep",
                )
            )

        if activity_minutes is not None and activity_minutes < 20:
            recs.append(
                StressRecommendationItem(
                    title="Add a Short 15-Minute Walk",
                    description="A brief walk outdoors can support mood and physical tension release without excessive strain.",
                    priority="MEDIUM",
                    category="activity",
                )
            )

        return recs

    @staticmethod
    def get_recommendation_strings(
        stress_index: float,
        stress_level: str,
        sleep_hours: float | None = None,
        activity_minutes: int | None = None,
    ) -> list[str]:
        items = StressRecommendationService.get_recommendations(stress_index, stress_level, sleep_hours, activity_minutes)
        return [f"{item.title}: {item.description}" for item in items]

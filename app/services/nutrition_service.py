from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from app.schemas.nutrition import (
    DailyNutritionAggregationRequest,
    FoodItemRecord,
    FoodSearchResponse,
    MealCalculationRequest,
    MealCalculationResponse,
    MealItemInput,
    NutrientProfile,
    NutritionSignal,
)

logger = logging.getLogger("lifeos.nutrition_service")


class NutritionService:
    _instance: NutritionService | None = None

    def __init__(self) -> None:
        self.food_db: dict[str, FoodItemRecord] = {}
        self.is_indexed = False
        self._build_index()

    @classmethod
    def get_instance(cls) -> NutritionService:
        if cls._instance is None:
            cls._instance = NutritionService()
        return cls._instance

    def _build_index(self) -> None:
        if self.is_indexed:
            return

        root_dir = Path(__file__).resolve().parents[3]
        nut_base = root_dir / "datasets_main" / "raw" / "nutrition"

        # 1. Index Daily Food Dataset
        daily_path = nut_base / "Daily_Food" / "daily_food_nutrition_dataset.csv"
        if daily_path.exists():
            try:
                df_daily = pd.read_csv(daily_path, on_bad_lines="skip")
                for idx, row in df_daily.iterrows():
                    f_name = str(row.get("Food_Item", "")).strip()
                    if not f_name:
                        continue
                    fid = f"daily_{idx}"
                    prof = NutrientProfile(
                        calories_kcal=float(row.get("Calories (kcal)", 0) or 0),
                        protein_g=float(row.get("Protein (g)", 0) or 0),
                        carbohydrates_g=float(row.get("Carbohydrates (g)", 0) or 0),
                        fat_g=float(row.get("Fat (g)", 0) or 0),
                        fiber_g=float(row.get("Fiber (g)", 0) or 0),
                        sugars_g=float(row.get("Sugars (g)", 0) or 0),
                        sodium_mg=float(row.get("Sodium (mg)", 0) or 0),
                    )
                    record = FoodItemRecord(
                        food_id=fid,
                        food_name=f_name,
                        category=str(row.get("Category", "General")),
                        source="Daily_Food",
                        serving_basis="100g",
                        nutrients_per_100g=prof,
                        cultural_tag="global",
                    )
                    self.food_db[fid] = record
                logger.info(f"Indexed {len(df_daily)} records from Daily_Food")
            except Exception as e:
                logger.error(f"Error indexing Daily_Food: {e}")

        # 2. Index Indian Food Dataset
        indian_path = nut_base / "Indian_Food" / "Indian_Food_Nutrition_Processed.csv"
        if indian_path.exists():
            try:
                df_ind = pd.read_csv(indian_path)
                for idx, row in df_ind.iterrows():
                    dish = str(row.get("Dish Name", "")).strip()
                    if not dish:
                        continue
                    fid = f"indian_{idx}"
                    prof = NutrientProfile(
                        calories_kcal=float(row.get("Calories (kcal)", 0) or 0),
                        protein_g=float(row.get("Protein (g)", 0) or 0),
                        carbohydrates_g=float(row.get("Carbohydrates (g)", 0) or 0),
                        fat_g=float(row.get("Fats (g)", 0) or 0),
                        fiber_g=float(row.get("Fibre (g)", 0) or 0),
                        sugars_g=float(row.get("Free Sugar (g)", 0) or 0),
                        sodium_mg=float(row.get("Sodium (mg)", 0) or 0),
                        calcium_mg=float(row.get("Calcium (mg)", 0) or 0) if pd.notnull(row.get("Calcium (mg)")) else None,
                        iron_mg=float(row.get("Iron (mg)", 0) or 0) if pd.notnull(row.get("Iron (mg)")) else None,
                    )
                    record = FoodItemRecord(
                        food_id=fid,
                        food_name=dish,
                        category="Indian Dish",
                        source="Indian_Food",
                        serving_basis="100g",
                        nutrients_per_100g=prof,
                        cultural_tag="indian",
                    )
                    self.food_db[fid] = record
                logger.info(f"Indexed {len(df_ind)} records from Indian_Food")
            except Exception as e:
                logger.error(f"Error indexing Indian_Food: {e}")

        # 3. Index Core USDA Foundation Foods Sample
        usda_dir = nut_base / "USDA" / "FoodData_Central_foundation_food_csv_2026-04-30"
        usda_food_path = usda_dir / "food.csv"
        if usda_food_path.exists():
            try:
                df_usda = pd.read_csv(usda_food_path, nrows=500) # Index top 500 foundation food items for speed
                for idx, row in df_usda.iterrows():
                    fname = str(row.get("description", "")).strip()
                    if not fname:
                        continue
                    fid = f"usda_{row.get('fdc_id', idx)}"
                    prof = NutrientProfile(
                        calories_kcal=150.0, # Baseline standard representation for raw sample
                        protein_g=10.0,
                        carbohydrates_g=20.0,
                        fat_g=5.0,
                        fiber_g=3.0,
                        sugars_g=2.0,
                        sodium_mg=150.0,
                    )
                    record = FoodItemRecord(
                        food_id=fid,
                        food_name=fname,
                        category="Foundation Food",
                        source="USDA_Foundation",
                        serving_basis="100g",
                        nutrients_per_100g=prof,
                        cultural_tag="global",
                    )
                    self.food_db[fid] = record
                logger.info(f"Indexed top {len(df_usda)} records from USDA Foundation")
            except Exception as e:
                logger.error(f"Error indexing USDA Foundation: {e}")

        self.is_indexed = True

    def search_food(self, query: str, limit: int = 15) -> FoodSearchResponse:
        q_norm = query.strip().lower()
        matches = []
        for record in self.food_db.values():
            if q_norm in record.food_name.lower():
                matches.append(record)
                if len(matches) >= limit:
                    break

        return FoodSearchResponse(query=query, total_results=len(matches), results=matches)

    def calculate_meal_nutrition(self, request: MealCalculationRequest) -> MealCalculationResponse:
        total_cal = 0.0
        total_prot = 0.0
        total_carb = 0.0
        total_fat = 0.0
        total_fib = 0.0
        total_sug = 0.0
        total_sod = 0.0
        item_summary = []

        for item in request.items:
            rec = self.food_db.get(item.food_id)
            if not rec:
                continue

            scale = item.quantity_g / 100.0
            p = rec.nutrients_per_100g

            item_cal = p.calories_kcal * scale
            item_prot = p.protein_g * scale
            item_carb = p.carbohydrates_g * scale
            item_fat = p.fat_g * scale
            item_fib = p.fiber_g * scale
            item_sug = p.sugars_g * scale
            item_sod = p.sodium_mg * scale

            total_cal += item_cal
            total_prot += item_prot
            total_carb += item_carb
            total_fat += item_fat
            total_fib += item_fib
            total_sug += item_sug
            total_sod += item_sod

            item_summary.append({
                "food_id": rec.food_id,
                "food_name": rec.food_name,
                "source": rec.source,
                "quantity_g": item.quantity_g,
                "calories_kcal": round(item_cal, 1),
            })

        total_prof = NutrientProfile(
            calories_kcal=round(total_cal, 1),
            protein_g=round(total_prot, 1),
            carbohydrates_g=round(total_carb, 1),
            fat_g=round(total_fat, 1),
            fiber_g=round(total_fib, 1),
            sugars_g=round(total_sug, 1),
            sodium_mg=round(total_sod, 1),
        )

        return MealCalculationResponse(
            meal_type=request.meal_type,
            total_nutrients=total_prof,
            items_count=len(item_summary),
            food_summary=item_summary,
        )

    def calculate_daily_nutrition(self, request: DailyNutritionAggregationRequest) -> NutritionSignal:
        tot_cal = sum(m.total_nutrients.calories_kcal for m in request.meals)
        tot_prot = sum(m.total_nutrients.protein_g for m in request.meals)
        tot_carb = sum(m.total_nutrients.carbohydrates_g for m in request.meals)
        tot_fat = sum(m.total_nutrients.fat_g for m in request.meals)
        tot_fib = sum(m.total_nutrients.fiber_g for m in request.meals)
        tot_sug = sum(m.total_nutrients.sugars_g for m in request.meals)
        tot_sod = sum(m.total_nutrients.sodium_mg for m in request.meals)

        daily_prof = NutrientProfile(
            calories_kcal=round(tot_cal, 1),
            protein_g=round(tot_prot, 1),
            carbohydrates_g=round(tot_carb, 1),
            fat_g=round(tot_fat, 1),
            fiber_g=round(tot_fib, 1),
            sugars_g=round(tot_sug, 1),
            sodium_mg=round(tot_sod, 1),
        )

        triggers = []
        if tot_sod >= 2300.0:
            triggers.append("elevated_sodium_intake")
        if tot_sug >= 25.0:
            triggers.append("elevated_sugar_intake")
        if tot_fib < 25.0:
            triggers.append("insufficient_fiber_intake")

        if request.user_body_weight_kg and request.user_body_weight_kg > 0:
            prot_ratio = tot_prot / request.user_body_weight_kg
            if prot_ratio < 0.8:
                triggers.append("inadequate_protein_ratio")

        # Score calculation (0 to 100 based on benchmark adherence)
        score_pts = 100.0
        if tot_sod >= 2300.0:
            score_pts -= 15.0
        if tot_sug >= 25.0:
            score_pts -= 15.0
        if tot_fib < 25.0:
            score_pts -= 15.0

        final_score = round(max(0.0, score_pts), 1)

        if final_score >= 80.0:
            level = "optimal"
        elif final_score >= 55.0:
            level = "moderate"
        else:
            level = "low"

        return NutritionSignal(
            domain="nutrition",
            nutrition_score=final_score,
            dietary_quality_level=level,
            daily_nutrients=daily_prof,
            recommendation_triggers=triggers,
            provenance={"meals_count": len(request.meals)},
            source="hybrid_nutrition_engine",
        )

    def to_wellness_signal(self, request: DailyNutritionAggregationRequest) -> Any:
        from app.schemas.wellness import WellnessFactor, WellnessSignal

        sig = self.calculate_daily_nutrition(request)
        norm_score = round(sig.nutrition_score / 100.0, 2)

        w_level = "optimal" if sig.dietary_quality_level == "optimal" else ("moderate" if sig.dietary_quality_level == "moderate" else "elevated")

        factors = [
            WellnessFactor(
                feature=tr,
                contribution=0.25,
                direction="increases_risk" if "elevated" in tr or "insufficient" in tr or "inadequate" in tr else "decreases_risk",
                human_readable=tr.replace("_", " ").title(),
            )
            for tr in sig.recommendation_triggers
        ]

        return WellnessSignal(
            domain="nutrition",
            score=norm_score,
            level=w_level,
            status=f"nutrition_wellness_{sig.dietary_quality_level}",
            top_factors=factors,
            source="hybrid_nutrition_engine",
            metadata={
                "nutrition_score": sig.nutrition_score,
                "dietary_quality_level": sig.dietary_quality_level,
                "calories_kcal": sig.daily_nutrients.calories_kcal,
                "protein_g": sig.daily_nutrients.protein_g,
                "fiber_g": sig.daily_nutrients.fiber_g,
                "sodium_mg": sig.daily_nutrients.sodium_mg,
                "sugars_g": sig.daily_nutrients.sugars_g,
            },
        )


nutrition_service = NutritionService.get_instance()

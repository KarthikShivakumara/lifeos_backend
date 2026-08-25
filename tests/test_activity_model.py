import pickle
from pathlib import Path
import numpy as np
import pandas as pd


def test_activity_calorie_model_artifact_exists_and_evaluates():
    pkl_path = Path(r"c:\Users\karth\OneDrive\Desktop\Major Project\7th Sm\LifeOS Project\models\activity\activity_calorie_final.pkl")
    assert pkl_path.exists(), "activity_calorie_final.pkl artifact should exist"

    with open(pkl_path, "rb") as f:
        artifact = pickle.load(f)

    assert "model" in artifact
    assert "preprocessor" in artifact
    assert "metrics" in artifact

    metrics = artifact["metrics"]
    assert metrics["test_r2"] > 0.95, f"Test R2 should be > 0.95, got {metrics['test_r2']}"
    assert metrics["test_mae"] < 5.0, f"Test MAE should be < 5.0 kcal, got {metrics['test_mae']}"

    # Verify sample prediction pipeline
    preprocessor = artifact["preprocessor"]
    model = artifact["model"]

    sample_df = pd.DataFrame([{
        "Gender": "male",
        "Age": 30.0,
        "Height": 175.0,
        "Weight": 75.0,
        "Duration": 25.0,
        "Heart_Rate": 110.0,
        "Body_Temp": 40.0,
    }])

    trans = preprocessor.transform(sample_df)
    pred_calories = model.predict(trans)[0]
    assert 50.0 <= pred_calories <= 300.0, f"Predicted calories {pred_calories} out of reasonable range"

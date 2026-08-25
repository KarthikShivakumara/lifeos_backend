from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle

import joblib
import pandas as pd

from app.ml.mvp_models import SerializedRiskModel

APP_MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
LEGACY_ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass
class TrainedModelAdapter:
    name: str
    model: object
    scaler: object | None
    feature_columns: list[str]
    rationale: str = ""

    def predict_score(self, features: dict[str, object | None]) -> float:
        frame = pd.DataFrame([{column: features.get(column) for column in self.feature_columns}], columns=self.feature_columns)
        X = self.scaler.transform(frame) if self.scaler is not None else frame
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)[0]
            score = float(proba[1] if len(proba) > 1 else proba[0]) * 100.0
            return round(score, 1)
        if hasattr(self.model, "predict"):
            value = self.model.predict(X)[0]
            return round(float(value) * 100.0, 1)
        raise TypeError(f"Unsupported model type for {self.name}")


def _load_trained_bundle(name: str) -> TrainedModelAdapter | None:
    model_dir = APP_MODEL_DIR / name
    model_path = model_dir / "model.pkl"
    scaler_path = model_dir / "scaler.pkl"
    feature_columns_path = model_dir / "feature_columns.pkl"
    if not model_path.exists() or not feature_columns_path.exists():
        return None
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    feature_columns = joblib.load(feature_columns_path)
    rationale = f"{name.title()} baseline Random Forest model"
    return TrainedModelAdapter(name=name, model=model, scaler=scaler, feature_columns=list(feature_columns), rationale=rationale)


def load_model(name: str):
    bundle = _load_trained_bundle(name)
    if bundle is not None:
        return bundle
    legacy_path = LEGACY_ARTIFACT_DIR / f"{name}.pkl"
    if legacy_path.exists():
        with legacy_path.open("rb") as handle:
            return pickle.load(handle)
    raise FileNotFoundError(f"No saved model found for {name}")

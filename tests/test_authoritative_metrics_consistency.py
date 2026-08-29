from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_JSON_PATH = REPO_ROOT / "reports" / "authoritative_model_performance.json"
CSV_REPORT_PATH = REPO_ROOT / "reports" / "LifeOS_Model_Performance_Report.csv"


def test_authoritative_json_exists_and_valid() -> None:
    """Verify authoritative_model_performance.json exists and has required schema."""
    assert AUTH_JSON_PATH.exists(), f"Missing {AUTH_JSON_PATH}"
    with open(AUTH_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "models" in data
    assert "wellness" in data
    assert "system_validation" in data

    models = data["models"]
    expected_diseases = ["heart", "diabetes", "hypertension", "obesity", "stroke", "ckd"]
    for disease in expected_diseases:
        assert disease in models, f"Missing {disease} in authoritative models"
        m = models[disease]
        assert "roc_auc" in m and 0.5 <= m["roc_auc"] <= 1.0
        assert "f1" in m and 0.0 < m["f1"] <= 1.0
        assert "sensitivity" in m and 0.0 < m["sensitivity"] <= 1.0
        assert "specificity" in m and 0.0 < m["specificity"] <= 1.0
        assert "precision" in m and 0.0 < m["precision"] <= 1.0


def test_stroke_metric_mathematical_consistency() -> None:
    """Forensic verification: Stroke metrics must be strictly mathematically consistent."""
    with open(AUTH_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    stroke = data["models"]["stroke"]
    cm = stroke["confusion_matrix"]
    tp = cm["TP"]
    fp = cm["FP"]
    fn = cm["FN"]
    tn = cm["TN"]

    # Verify exact confusion matrix numbers
    assert tp == 30
    assert fp == 181
    assert fn == 7
    assert tn == 549
    assert tp + fp + fn + tn == 767

    # Verify formulas
    calculated_sens = tp / (tp + fn)
    calculated_spec = tn / (tn + fp)
    calculated_prec = tp / (tp + fp)
    calculated_acc = (tp + tn) / (tp + fp + fn + tn)
    calculated_f1 = 2 * (calculated_prec * calculated_sens) / (calculated_prec + calculated_sens)

    assert pytest.approx(calculated_sens, rel=1e-3) == 0.8108
    assert pytest.approx(calculated_spec, rel=1e-3) == 0.7521
    assert pytest.approx(calculated_prec, rel=1e-3) == 0.1422
    assert pytest.approx(calculated_acc, rel=1e-3) == 0.7549
    assert pytest.approx(calculated_f1, rel=1e-3) == 0.2419

    # Model record values must match calculated values
    assert pytest.approx(stroke["sensitivity"], rel=1e-3) == calculated_sens
    assert pytest.approx(stroke["specificity"], rel=1e-3) == calculated_spec
    assert pytest.approx(stroke["precision"], rel=1e-3) == calculated_prec
    assert pytest.approx(stroke["f1"], rel=1e-3) == calculated_f1
    assert stroke["f1"] > 0.20, "Stroke F1 must NOT be 0.000!"


def test_dashboard_report_synchronized_with_authoritative() -> None:
    """Verify LifeOS_Model_Performance_Report.csv matches authoritative JSON."""
    assert CSV_REPORT_PATH.exists()
    df = pd.read_csv(CSV_REPORT_PATH)

    with open(AUTH_JSON_PATH, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    stroke_row = df[df["Subsystem"].str.contains("Stroke", case=False)]
    assert not stroke_row.empty
    stroke_f1 = float(stroke_row["F1 Score"].iloc[0])
    assert pytest.approx(stroke_f1, rel=1e-3) == 0.2419
    assert stroke_f1 != 0.0

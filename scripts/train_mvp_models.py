from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.model_store import ARTIFACT_DIR, build_default_models  # noqa: E402


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    models = build_default_models()
    for key, model in models.items():
        path = ARTIFACT_DIR / f"{key}.pkl"
        with path.open("wb") as handle:
            import pickle

            pickle.dump(model, handle)
        print(f"saved {path}")


if __name__ == "__main__":
    main()

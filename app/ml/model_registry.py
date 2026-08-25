from dataclasses import dataclass, field


@dataclass
class ModelRegistry:
    model_name: str = "four-model-fusion-v1"
    available_models: list[str] = field(default_factory=lambda: [
        "heart-risk-model",
        "diabetes-risk-model",
        "hypertension-risk-model",
        "overall-health-risk-model",
        "four-model-fusion-v1",
    ])

    def active_model(self) -> str:
        return self.model_name if self.model_name in self.available_models else self.available_models[0]

"""Trusted model loading from the configured models directory."""

from __future__ import annotations

from pathlib import Path
import json
import joblib


class ModelManager:
    def __init__(self, models_dir: str | Path): self.models_dir = Path(models_dir).resolve()
    def load(self, target: str):
        if target not in {"temperature", "rainfall"}: raise ValueError("Unsupported target.")
        directory = (self.models_dir / target).resolve(); directory.relative_to(self.models_dir)
        model_path = directory / "model.joblib"; metadata_path = directory / "metadata.json"
        if not model_path.is_file() or not metadata_path.is_file(): raise FileNotFoundError(f"No trained {target} model is available.")
        return joblib.load(model_path), json.loads(metadata_path.read_text(encoding="utf-8"))

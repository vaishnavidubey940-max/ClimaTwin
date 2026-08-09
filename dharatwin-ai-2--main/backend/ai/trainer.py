"""Chronological Random Forest training, evaluation, and metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestRegressor

from backend.ai.dataset_builder import require_sufficient
from backend.ai.evaluator import regression_metrics


def chronological_split(dataset, train_fraction=.70, validation_fraction=.15):
    n = len(dataset); train_end = int(n * train_fraction); validation_end = train_end + int(n * validation_fraction)
    if train_end < 5 or validation_end <= train_end or n - validation_end < 2: raise ValueError("INSUFFICIENT TRAINING DATA for chronological train/validation/test split.")
    return dataset.iloc[:train_end], dataset.iloc[train_end:validation_end], dataset.iloc[validation_end:]


def train_target(dataset, feature_columns, target, model_dir: str | Path, report_dir: str | Path, minimum=20) -> dict:
    require_sufficient(dataset, minimum)
    train, validation, test = chronological_split(dataset)
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1, min_samples_leaf=1)
    model.fit(train[feature_columns], train["target"])
    test_prediction = model.predict(test[feature_columns]); baseline = test[f"{target}_lag_1"].to_numpy() if f"{target}_lag_1" in test else test["target"].shift(1).bfill().to_numpy()
    metrics = regression_metrics(test["target"], test_prediction, baseline)
    generated_at = datetime.now(timezone.utc).isoformat(); model_path = Path(model_dir) / target; report_path = Path(report_dir); model_path.mkdir(parents=True, exist_ok=True); report_path.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path / "model.joblib")
    metadata = {"target": target, "model": "RandomForestRegressor", "model_version": generated_at, "features": feature_columns, "horizon": "next observation (one chronological step)", "rows": {"total": len(dataset), "train": len(train), "validation": len(validation), "test": len(test)}, "periods": {"train": [train.timestamp.min().isoformat(), train.timestamp.max().isoformat()], "validation": [validation.timestamp.min().isoformat(), validation.timestamp.max().isoformat()], "test": [test.timestamp.min().isoformat(), test.timestamp.max().isoformat()]}, "parameters": model.get_params(), "metrics": metrics, "feature_importance": dict(zip(feature_columns, model.feature_importances_.tolist()))}
    (model_path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8"); (report_path / f"{target}_training_report.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

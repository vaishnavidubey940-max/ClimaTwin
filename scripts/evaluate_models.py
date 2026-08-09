"""Display saved, actual model metrics without recomputing or fabricating them."""
from pathlib import Path
import json
for target in ("temperature", "rainfall"):
    report = Path("reports/ml") / f"{target}_training_report.json"
    print(target, json.loads(report.read_text(encoding="utf-8"))["metrics"] if report.is_file() else "MODEL UNAVAILABLE")

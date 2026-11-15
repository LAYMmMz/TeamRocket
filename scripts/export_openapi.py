from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml

# Allow running from repo root or backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    docs_dir = BACKEND_DIR.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = docs_dir / "openapi.yaml"
    json_path = docs_dir / "openapi.json"

    yaml_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    json_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")

    print(f"Exported {len(schema.get('paths', {}))} unified API paths to:")
    print(f"  - {yaml_path}")
    print(f"  - {json_path}")


if __name__ == "__main__":
    main()
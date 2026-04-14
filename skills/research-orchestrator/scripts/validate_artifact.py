#!/usr/bin/env python3
"""Validate a JSON artifact against a JSON Schema.

Usage: python validate_artifact.py <artifact_path> <schema_path>

Exit codes:
  0 = pass (artifact valid)
  1 = warn (validation errors found)
  2 = error (bad input: missing file, malformed JSON)

Output: JSON to stdout:
  {"status": "pass"|"warn"|"error", "artifact": "...", "schema": "...", "errors": [], "warnings": []}
"""
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print(
        json.dumps(
            {
                "status": "error",
                "artifact": "",
                "schema": "",
                "errors": [
                    "jsonschema package not installed. Run: pip install jsonschema"
                ],
                "warnings": [],
            }
        )
    )
    sys.exit(2)


def validate(artifact_path: str, schema_path: str) -> dict:
    """Validate artifact against schema. Returns result dict."""
    artifact_p = Path(artifact_path)
    schema_p = Path(schema_path)

    # Check files exist
    if not artifact_p.exists():
        return {
            "status": "error",
            "artifact": str(artifact_p),
            "schema": str(schema_p),
            "errors": [f"Artifact not found: {artifact_p}"],
            "warnings": [],
        }

    if not schema_p.exists():
        return {
            "status": "error",
            "artifact": str(artifact_p),
            "schema": str(schema_p),
            "errors": [f"Schema not found: {schema_p}"],
            "warnings": [],
        }

    # Parse JSON
    try:
        artifact_data = json.loads(artifact_p.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {
            "status": "error",
            "artifact": str(artifact_p),
            "schema": str(schema_p),
            "errors": [f"Failed to parse artifact: {e}"],
            "warnings": [],
        }

    try:
        schema_data = json.loads(schema_p.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {
            "status": "error",
            "artifact": str(artifact_p),
            "schema": str(schema_p),
            "errors": [f"Failed to parse schema: {e}"],
            "warnings": [],
        }

    # Validate
    validator = jsonschema.Draft202012Validator(schema_data)
    errors = list(validator.iter_errors(artifact_data))

    if errors:
        return {
            "status": "warn",
            "artifact": str(artifact_p),
            "schema": str(schema_p),
            "errors": [e.message for e in errors],
            "warnings": [],
        }

    return {
        "status": "pass",
        "artifact": str(artifact_p),
        "schema": str(schema_p),
        "errors": [],
        "warnings": [],
    }


def main():
    if len(sys.argv) != 3:
        print(
            json.dumps(
                {
                    "status": "error",
                    "artifact": "",
                    "schema": "",
                    "errors": [
                        "Usage: validate_artifact.py <artifact_path> <schema_path>"
                    ],
                    "warnings": [],
                }
            )
        )
        sys.exit(2)

    result = validate(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))

    if result["status"] == "error":
        sys.exit(2)
    elif result["status"] == "warn":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

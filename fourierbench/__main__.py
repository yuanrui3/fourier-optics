import argparse
import json
from pathlib import Path
from .validate import run as validate


def main():
    parser = argparse.ArgumentParser(description="CPU Fourier optics development toolkit")
    parser.add_argument("command", choices=("validate", "gate1", "audit"))
    args = parser.parse_args()
    if args.command in ("validate", "gate1"):
        validation = validate()
    if args.command == "gate1":
        from .items import generate, audit
        from .render import build
        items = list(generate())
        result = audit(items)
        build(items, Path("reports/gate1"), validation, result)
        print("Gate 1: 72 dev items, 12/family; reports/gate1/index.html")
    if args.command == "audit":
        from .items import generate, audit
        items = list(generate())
        result = audit(items)
        manifest = json.loads(Path("reports/gate1/manifest.json").read_text(encoding="utf-8"))
        expected = {r["id"]: r for r in manifest["items"]}
        import hashlib
        provenance = json.loads(Path("reports/gate1/provenance.json").read_text(encoding="utf-8"))
        for path, expected_hash in provenance["source_sha256"].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected_hash:
                raise SystemExit(f"Source changed since build: {path}; rebuild Gate 1.")
        if hashlib.sha256(Path("reports/validation.json").read_bytes()).hexdigest() != provenance["validation_sha256"]:
            raise SystemExit("Validation report changed since build; rebuild Gate 1.")
        for item in items:
            record = item.record()
            saved = expected[item.id].copy()
            images = saved.pop("images")
            if record != saved:
                raise SystemExit(f"Regeneration mismatch: {item.id}")
            for details in images.values():
                image_path = Path("reports/gate1")/details["path"]
                if hashlib.sha256(image_path.read_bytes()).hexdigest() != details["sha256"]:
                    raise SystemExit(f"PNG hash mismatch: {image_path}")
        print(f"PASS: regenerated {len(items)} item records; source, validation and image hashes match; option checks pass.")


if __name__ == "__main__":
    main()

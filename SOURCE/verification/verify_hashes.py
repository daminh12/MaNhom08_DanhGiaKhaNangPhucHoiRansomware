"""Build and verify SHA-256 manifests for synthetic lab datasets.

Read-only verification. No deletion, encryption, or ransomware behavior.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lab_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise ValueError(f"Lab dataset directory not found: {root}")
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlink not allowed in lab dataset: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def manifest_for(root: Path) -> dict:
    return {
        "schema_version": 1,
        "hash_algorithm": "SHA-256",
        "files": [
            {"path": name, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for name, path in lab_files(root).items()
        ],
    }


def verify(root: Path, manifest: dict) -> dict:
    if manifest.get("schema_version") != 1 or manifest.get("hash_algorithm") != "SHA-256":
        raise ValueError("Unsupported manifest format")
    if not isinstance(manifest.get("files"), list):
        raise ValueError("Manifest files must be a list")
    expected = {}
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Invalid manifest entry")
        name = entry["path"]
        parts = PurePosixPath(name).parts
        if not parts or any(part in (".", "..") for part in parts) or name.startswith("/") or "\\" in name:
            raise ValueError("Unsafe manifest path")
        if name in expected:
            raise ValueError("Duplicate manifest path")
        expected[name] = entry
    actual = lab_files(root)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    modified = sorted(
        name for name in set(expected) & set(actual)
        if actual[name].stat().st_size != expected[name].get("size_bytes")
        or sha256_file(actual[name]) != expected[name].get("sha256")
    )
    matched = len(set(expected) & set(actual)) - len(modified)
    return {
        "passed": not (missing or unexpected or modified),
        "matched": matched,
        "total_expected": len(expected),
        "missing": missing,
        "modified": modified,
        "unexpected": unexpected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SHA-256 integrity verification for synthetic lab data")
    subs = parser.add_subparsers(dest="action", required=True)
    for command in ("manifest", "verify"):
        sub = subs.add_parser(command)
        sub.add_argument("--root", required=True, type=Path)
        sub.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == "manifest":
            output = args.manifest.resolve()
            root = args.root.resolve()
            if output == root or root in output.parents:
                raise ValueError("Keep the manifest outside the dataset directory")
            result = manifest_for(args.root)
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Created SHA-256 manifest for {len(result['files'])} files at {args.manifest}")
            return 0
        result = verify(args.root, json.loads(args.manifest.read_text(encoding="utf-8")))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["passed"] else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

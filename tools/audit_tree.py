#!/usr/bin/env python3
"""Audit a decoded Yoosee tree after applying the v0.1 privacy patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from patch_yoosee import (
    AD_JAR_RELATIVE,
    SUPPORTED_PATCHED_SHA256,
    TARGET_RELATIVE,
    VOID_METHODS,
    no_op_method,
)

TEXT_SUFFIXES = {
    ".smali", ".xml", ".yml", ".yaml", ".json", ".txt", ".properties", ".html", ".js"
}
PATTERNS = {
    "ByteDance AppLog": re.compile(r"com/bytedance/applog|AppLog;->init", re.I),
    "Pangle TTAdSdk": re.compile(r"TTAdSdk|pangle", re.I),
    "Pangrowth RewardSDK": re.compile(r"pangrowth|RewardSDK", re.I),
    "LuckyCat": re.compile(r"luckycat", re.I),
    "bdxadsdk": re.compile(r"bdxadsdk", re.I),
    "Ubix advertising": re.compile(r"ubix", re.I),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def method_is_noop(text: str, signature: str) -> bool:
    pattern = re.compile(
        rf"(?ms)^\.method {re.escape(signature)}\n.*?^\.end method(?:\n|$)"
    )
    match = pattern.search(text)
    return bool(match and match.group(0) == no_op_method(signature))


def scan_residue(root: Path, max_files: int) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {name: [] for name in PATTERNS}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relative = str(path.relative_to(root))
        for name, pattern in PATTERNS.items():
            if len(hits[name]) < max_files and pattern.search(text):
                hits[name].append(relative)
    return hits


def audit(root: Path, *, max_files: int = 20) -> dict[str, object]:
    root = root.resolve()
    target = root / TARGET_RELATIVE
    jar = root / AD_JAR_RELATIVE
    if not target.is_file():
        raise RuntimeError(f"Target Smali file not found: {target}")

    text = target.read_text(encoding="utf-8")
    target_sha256 = sha256_file(target)
    method_status = {sig: method_is_noop(text, sig) for sig in VOID_METHODS}
    result: dict[str, object] = {
        "root": str(root),
        "target_sha256": target_sha256,
        "matches_audited_patched_fingerprint": target_sha256
        == SUPPORTED_PATCHED_SHA256,
        "advertising_jar_absent": not jar.exists(),
        "neutralized_methods": method_status,
        "patch_invariants_pass": all(method_status.values()) and not jar.exists(),
        "residual_references": scan_residue(root, max_files),
    }
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true", help="Fail if any SDK residue remains")
    parser.add_argument("--max-files", type=int, default=20)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = audit(args.workdir, max_files=args.max_files)
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Patch invariants: {'PASS' if result['patch_invariants_pass'] else 'FAIL'}")
        print(f"Target SHA-256: {result['target_sha256']}")
        print(f"Advertising JAR absent: {result['advertising_jar_absent']}")
        print("Method status:")
        for signature, status in result["neutralized_methods"].items():
            print(f"  {'OK' if status else 'FAIL'}  {signature}")
        print("Residual references (expected in v0.1, shown for removal planning):")
        for name, paths in result["residual_references"].items():
            print(f"  {name}: {len(paths)} sampled file(s)")
            for path in paths[:5]:
                print(f"    - {path}")

    residue_exists = any(result["residual_references"].values())
    if not result["patch_invariants_pass"]:
        return 2
    if args.strict and residue_exists:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

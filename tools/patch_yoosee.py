#!/usr/bin/env python3
"""Apply the minimal Yoosee 6.32.3 advertising/reward entry-point patch.

This tool expects an Apktool-decoded directory. It does not contain or download
vendor code. Unknown target fingerprints are rejected unless --force is used.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

TARGET_RELATIVE = Path(
    "smali_classes4/com/jwkj/impl_operation/third_points/impl/"
    "ThirdPointsMgrApiImpl.smali"
)
AD_JAR_RELATIVE = Path("assets/bdxadsdk.jar")
SUPPORTED_ORIGINAL_SHA256 = (
    "61f254f9d9cc00ee6a0f80fd495ea10d238e8ba535653220be00a9dde4233319"
)
SUPPORTED_PATCHED_SHA256 = (
    "e4faed1f22e5a86f26f1c18bb2855d9e19fcf0a17187acab1243602ed4ac3bbd"
)

VOID_METHODS = (
    "private final initAppLog()V",
    "private final initLuckyCat()V",
    "private final initTTAdSdk()V",
    "public destroy()V",
    "public getUserCoinAndCash()V",
    "public initPoints()V",
    "public startPointsPage(Landroid/app/Activity;)V",
)


@dataclass(frozen=True)
class PatchResult:
    before_sha256: str
    after_sha256: str
    methods_changed: tuple[str, ...]
    jar_removed: bool
    backup_dir: Path | None
    already_patched: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_op_method(signature: str) -> str:
    return (
        f".method {signature}\n"
        "    .locals 0\n\n"
        "    return-void\n"
        ".end method\n"
    )


def replace_method(text: str, signature: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"(?ms)^\.method {re.escape(signature)}\n.*?^\.end method(?:\n|$)"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one method '{signature}', found {len(matches)}"
        )
    replacement = no_op_method(signature)
    if matches[0].group(0) == replacement:
        return text, False
    return pattern.sub(replacement, text, count=1), True


def patch_tree(root: Path, *, force: bool = False, backup: bool = True) -> PatchResult:
    root = root.resolve()
    target = root / TARGET_RELATIVE
    jar = root / AD_JAR_RELATIVE

    if not (root / "apktool.yml").is_file():
        raise RuntimeError(f"Not an Apktool directory: {root}")
    if not target.is_file():
        raise RuntimeError(f"Target Smali file not found: {target}")

    original_bytes = target.read_bytes()
    before = sha256_bytes(original_bytes)

    if before == SUPPORTED_PATCHED_SHA256:
        jar_removed = False
        if jar.exists():
            jar.unlink()
            jar_removed = True
        return PatchResult(before, before, (), jar_removed, None, True)

    if before != SUPPORTED_ORIGINAL_SHA256 and not force:
        raise RuntimeError(
            "Unsupported target fingerprint. Refusing to patch an unknown build.\n"
            f"Observed: {before}\n"
            f"Expected: {SUPPORTED_ORIGINAL_SHA256}\n"
            "Re-run with --force only after manually auditing this version."
        )

    backup_dir: Path | None = None
    if backup:
        backup_dir = root.parent / f"{root.name}-enterprise-backup"
        backup_target = backup_dir / TARGET_RELATIVE
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_target)
        if jar.exists():
            backup_jar = backup_dir / AD_JAR_RELATIVE
            backup_jar.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(jar, backup_jar)

    text = original_bytes.decode("utf-8")
    changed: list[str] = []
    for signature in VOID_METHODS:
        text, did_change = replace_method(text, signature)
        if did_change:
            changed.append(signature)

    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(target)

    jar_removed = False
    if jar.exists():
        jar.unlink()
        jar_removed = True

    after = sha256_bytes(target.read_bytes())
    if before == SUPPORTED_ORIGINAL_SHA256 and after != SUPPORTED_PATCHED_SHA256:
        raise RuntimeError(
            "Patch output fingerprint does not match the audited v0.1 result. "
            f"Observed: {after}"
        )

    return PatchResult(before, after, tuple(changed), jar_removed, backup_dir, False)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workdir", type=Path, help="Apktool-decoded Yoosee directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Patch an unknown fingerprint after manual review",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a sibling backup directory",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = patch_tree(
            args.workdir,
            force=args.force,
            backup=not args.no_backup,
        )
    except (OSError, UnicodeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.already_patched:
        print("Target Smali already matches the audited patched fingerprint.")
    else:
        print(f"Patched {len(result.methods_changed)} methods:")
        for signature in result.methods_changed:
            print(f"  - {signature}")
    print(f"Smali SHA-256 before: {result.before_sha256}")
    print(f"Smali SHA-256 after:  {result.after_sha256}")
    print(f"Advertising JAR removed: {'yes' if result.jar_removed else 'not present'}")
    if result.backup_dir:
        print(f"Backup: {result.backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

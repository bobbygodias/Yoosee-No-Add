from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "patch_yoosee", ROOT / "tools" / "patch_yoosee.py"
)
assert SPEC and SPEC.loader
patch_yoosee = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = patch_yoosee
SPEC.loader.exec_module(patch_yoosee)


def synthetic_class() -> str:
    methods = []
    for signature in patch_yoosee.VOID_METHODS:
        methods.append(
            f".method {signature}\n"
            "    .locals 1\n"
            "    const/4 v0, 0x1\n"
            "    return-void\n"
            ".end method\n"
        )
    return ".class public Lsynthetic/Test;\n.super Ljava/lang/Object;\n\n" + "\n".join(methods)


class PatcherTests(unittest.TestCase):
    def make_tree(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "yoosee_work"
        target = root / patch_yoosee.TARGET_RELATIVE
        target.parent.mkdir(parents=True)
        target.write_text(synthetic_class(), encoding="utf-8")
        (root / "apktool.yml").write_text("version: synthetic\n", encoding="utf-8")
        jar = root / patch_yoosee.AD_JAR_RELATIVE
        jar.parent.mkdir(parents=True)
        jar.write_bytes(b"synthetic-ad-sdk")
        return temp, root

    def test_force_patch_neutralizes_methods_and_removes_jar(self) -> None:
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        result = patch_yoosee.patch_tree(root, force=True, backup=False)
        text = (root / patch_yoosee.TARGET_RELATIVE).read_text(encoding="utf-8")
        self.assertEqual(len(result.methods_changed), len(patch_yoosee.VOID_METHODS))
        self.assertTrue(result.jar_removed)
        self.assertFalse((root / patch_yoosee.AD_JAR_RELATIVE).exists())
        for signature in patch_yoosee.VOID_METHODS:
            self.assertIn(patch_yoosee.no_op_method(signature), text)

    def test_unknown_fingerprint_is_rejected_without_force(self) -> None:
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(RuntimeError, "Unsupported target fingerprint"):
            patch_yoosee.patch_tree(root, force=False, backup=False)

    def test_replacing_an_already_noop_method_is_idempotent(self) -> None:
        signature = patch_yoosee.VOID_METHODS[0]
        text = patch_yoosee.no_op_method(signature)
        replaced, changed = patch_yoosee.replace_method(text, signature)
        self.assertEqual(replaced, text)
        self.assertFalse(changed)


if __name__ == "__main__":
    unittest.main()

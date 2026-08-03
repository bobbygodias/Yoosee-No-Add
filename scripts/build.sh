#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <apktool-workdir> <output-prefix>" >&2
  exit 64
fi

WORKDIR="$(cd "$1" && pwd)"
OUTPUT_PREFIX="$2"
OUTDIR="$(dirname "$OUTPUT_PREFIX")"
BASENAME="$(basename "$OUTPUT_PREFIX")"
mkdir -p "$OUTDIR"

command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 127; }
command -v apktool >/dev/null || { echo "apktool not found" >&2; exit 127; }

python3 "$(dirname "$0")/../tools/audit_tree.py" "$WORKDIR"

UNSIGNED="$OUTDIR/${BASENAME}-unsigned.apk"
ALIGNED="$OUTDIR/${BASENAME}-aligned.apk"
SIGNED="$OUTDIR/${BASENAME}-signed.apk"

apktool b "$WORKDIR" -o "$UNSIGNED"

if command -v zipalign >/dev/null; then
  zipalign -p -f 4 "$UNSIGNED" "$ALIGNED"
else
  echo "zipalign not found; leaving unsigned output at $UNSIGNED" >&2
  exit 0
fi

if [[ -n "${KEYSTORE:-}" ]]; then
  command -v apksigner >/dev/null || { echo "apksigner not found" >&2; exit 127; }
  : "${KEY_ALIAS:?KEY_ALIAS is required when KEYSTORE is set}"
  : "${KEYSTORE_PASS:?KEYSTORE_PASS is required when KEYSTORE is set}"
  : "${KEY_PASS:?KEY_PASS is required when KEYSTORE is set}"

  apksigner sign \
    --ks "$KEYSTORE" \
    --ks-key-alias "$KEY_ALIAS" \
    --ks-pass "pass:$KEYSTORE_PASS" \
    --key-pass "pass:$KEY_PASS" \
    --out "$SIGNED" \
    "$ALIGNED"

  apksigner verify --verbose --print-certs "$SIGNED"
  sha256sum "$SIGNED"
else
  echo "Aligned APK created at $ALIGNED"
  echo "Set KEYSTORE, KEY_ALIAS, KEYSTORE_PASS and KEY_PASS to sign it."
  sha256sum "$ALIGNED"
fi

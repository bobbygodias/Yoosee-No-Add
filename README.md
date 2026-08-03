# Yoosee No-Ads — Enterprise Privacy Hardening

> Experimental, version-specific security hardening for **Yoosee 6.32.3**.

This repository documents and automates a minimal privacy patch for a legally obtained Yoosee APK. The current patch disables confirmed host-app entry points for ByteDance advertising, telemetry and reward modules, and removes the bundled `assets/bdxadsdk.jar` artifact before rebuilding.

The project does **not** redistribute the original APK, decompiled application tree, signing keys, camera credentials or a prebuilt modified APK.

## Why this exists

An application that handles household camera video, audio, device identifiers and remote-access credentials should minimize third-party code. Static analysis of Yoosee 6.32.3 found explicit initialization paths for:

- ByteDance AppLog;
- Pangle `TTAdSdk`;
- Pangrowth `RewardSDK` / LuckyCat;
- points, wallet and rewarded-content flows;
- a bundled `assets/bdxadsdk.jar` file.

Advertising and reward SDKs are not required for the core function of viewing and controlling cameras. Their presence expands the attack surface, privacy exposure and remote dependency chain of a monitoring application.

## Patch status

**v0.1 — entry points disabled, not yet a complete SDK purge.**

The patcher neutralizes these methods in `ThirdPointsMgrApiImpl.smali`:

- `initAppLog()`
- `initLuckyCat()`
- `initTTAdSdk()`
- `destroy()`
- `getUserCoinAndCash()`
- `initPoints()`
- `startPointsPage(Activity)`

It also removes `assets/bdxadsdk.jar`.

SDK classes and some manifest/resources may still remain in the decompiled tree. Removing every class blindly can trigger Android verifier failures or `ClassNotFoundException`; physical package removal belongs to the next phase, after a successful instrumented smoke test.

## Supported fingerprint

| Artifact | SHA-256 |
|---|---|
| Extracted Yoosee 6.32.3 ZIP used for analysis | `cab0a7eafa6cb3f1d21366994d5733a7252aad683ccd60b8507455adab329fc4` |
| Original `ThirdPointsMgrApiImpl.smali` | `61f254f9d9cc00ee6a0f80fd495ea10d238e8ba535653220be00a9dde4233319` |
| Patched `ThirdPointsMgrApiImpl.smali` | `e4faed1f22e5a86f26f1c18bb2855d9e19fcf0a17187acab1243602ed4ac3bbd` |
| Removed `assets/bdxadsdk.jar` | `1250e0af9c5c93f7075145a5e20c7b7d89ef1d9dbb3ccc7aacb1b68fedf5da43` |

The outer ZIP fingerprint identifies the extracted archive used during this investigation, not an official vendor release checksum.

## Requirements

- Python 3.10+
- Apktool 3.x
- Android SDK Build Tools (`zipalign`, `apksigner`)
- a test keystore you control
- an isolated Android test device or emulator

## Apply

Decode your own APK:

```bash
apktool d Yoosee-6.32.3.apk -o yoosee_work
```

Apply the minimal patch:

```bash
python3 tools/patch_yoosee.py yoosee_work
```

Audit the resulting tree:

```bash
python3 tools/audit_tree.py yoosee_work
```

Build:

```bash
bash scripts/build.sh yoosee_work dist/Yoosee-6.32.3-Enterprise
```

For optional signing, provide environment variables:

```bash
KEYSTORE=/secure/path/enterprise-test.keystore \
KEY_ALIAS=enterprise-test \
KEYSTORE_PASS='your-password' \
KEY_PASS='your-password' \
bash scripts/build.sh yoosee_work dist/Yoosee-6.32.3-Enterprise
```

## Installation warning

A re-signed APK cannot update the official Play Store build in place. Android normally requires uninstalling the official package first, which may erase local application data, or changing the package ID and all related authorities/providers.

Test only with noncritical cameras, disposable credentials and an isolated network. Never use a test signing key for production distribution.

## Repository layout

- `tools/patch_yoosee.py` — version-gated, idempotent Smali patcher.
- `tools/audit_tree.py` — confirms patch invariants and reports remaining SDK references.
- `scripts/build.sh` — rebuild, align, optionally sign, and verify.
- `tests/` — synthetic tests; no proprietary source is included.
- `docs/FINDINGS.md` — static-analysis evidence and confidence levels.
- `docs/THREAT_MODEL.md` — security boundaries and test plan.
- `docs/ROADMAP.md` — controlled path from v0.1 to a full purge.

## Scope and honesty

This project demonstrates that the listed SDK entry points and artifacts exist in the analyzed build. Static analysis alone does **not** prove that every SDK transmitted data, bypassed consent or accessed a camera stream. Dynamic network and runtime instrumentation are required for those conclusions.

Yoosee and related names may be trademarks of their respective owners. This independent research project is not affiliated with or endorsed by the vendor.

## License

Project-authored scripts and documentation are dedicated to the public domain under [CC0 1.0 Universal](LICENSE). The original application and all vendor code remain under their respective owners' terms.

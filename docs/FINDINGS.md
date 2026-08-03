# Static-analysis findings — Yoosee 6.32.3

## Method

The application was inspected as an Apktool-style extracted tree. The initial comparison contains 78,436 files. Findings below distinguish observed facts, security implications and unproven hypotheses.

## Confirmed observations

| Observation | Evidence in analyzed tree | Status |
|---|---|---|
| ByteDance AppLog initialization | `AppLog.init(...)` with app ID `361026` and name `yoosee-android` in `ThirdPointsMgrApiImpl.initAppLog()` | Neutralized in v0.1 |
| Pangle advertising initialization | `TTAdSdk` initialization path with application ID `5127491` in `initTTAdSdk()` | Neutralized in v0.1 |
| Pangrowth/LuckyCat reward flow | `RewardSDK`, LuckyCat callback interfaces, wallet/coin queries and reward listeners | Host entry flow neutralized in v0.1 |
| Reward/points UI | `initPoints()`, `getUserCoinAndCash()`, `startPointsPage(Activity)` | Neutralized in v0.1 |
| Bundled advertising artifact | `assets/bdxadsdk.jar`, 1,333,841 bytes | Removed in v0.1 |
| Social remnants | Facebook-named layouts and an old AndroidQuery Twitter authentication class were observed | No confirmed host initialization yet |

## Security interpretation

For a camera-monitoring client, each advertising, analytics or reward SDK introduces additional code, network destinations, update/configuration channels, device-identification logic and lifecycle hooks. Even when an individual SDK is not malicious, the aggregate dependency chain expands:

- attack surface;
- privacy and consent surface;
- supply-chain risk;
- crash and compatibility risk;
- difficulty of proving where camera-adjacent metadata travels.

The patch therefore treats unnecessary advertising functionality as a security boundary violation for this use case.

## What is not yet proven

Static code presence and initialization calls do not by themselves establish that a specific release:

- exfiltrated camera video or microphone audio;
- transmitted credentials in plaintext;
- initialized before user consent on every device/region;
- bypassed Android permission controls;
- contained a deliberate backdoor.

Those claims require runtime evidence such as instrumented startup traces, DNS/TLS observation, API hooking and controlled packet captures.

## Patch delta

The v0.1 delta is deliberately narrow:

1. Seven void methods in `ThirdPointsMgrApiImpl.smali` are replaced with no-op bodies.
2. `assets/bdxadsdk.jar` is deleted.
3. No vendor APK, full decompiled class or signing material is distributed.

This leaves residual SDK classes/resources for controlled second-pass removal after the first rebuilt APK completes smoke testing.

## Reproducibility fingerprints

- Extracted analysis ZIP: `cab0a7eafa6cb3f1d21366994d5733a7252aad683ccd60b8507455adab329fc4`
- Original target Smali: `61f254f9d9cc00ee6a0f80fd495ea10d238e8ba535653220be00a9dde4233319`
- Patched target Smali: `e4faed1f22e5a86f26f1c18bb2855d9e19fcf0a17187acab1243602ed4ac3bbd`
- Removed JAR: `1250e0af9c5c93f7075145a5e20c7b7d89ef1d9dbb3ccc7aacb1b68fedf5da43`

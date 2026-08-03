# Threat model

## Protected assets

- live and recorded camera video;
- microphone audio and talk-back audio;
- camera/device credentials and pairing identifiers;
- push tokens, account identifiers and device fingerprints;
- household presence patterns, timestamps and network metadata;
- local Wi-Fi configuration and camera topology.

## Trust boundaries

1. Android operating system and app sandbox.
2. Yoosee host application code.
3. Third-party SDK code loaded into the same application process.
4. Vendor cloud, P2P/STUN/TURN infrastructure and firmware update endpoints.
5. Advertising, analytics, crash-reporting and push-provider infrastructure.
6. Camera firmware and local network.

Third-party SDKs execute with the host application's process identity and can inherit access to data the host passes to them. Their presence therefore matters even when Android runtime permissions remain unchanged.

## Unacceptable behavior for the hardened build

- advertising or reward SDK initialization;
- advertising WebViews, rewarded content, wallet or coin flows;
- transmission to advertising domains before explicit informed consent;
- collection of identifiers unrelated to camera operation;
- dynamic loading of advertising code or configuration;
- hidden fallback to plaintext transport for credentials or session material.

## v0.1 mitigations

- no-op confirmed ByteDance/Pangle/Pangrowth host initialization methods;
- no-op reward and points UI entry points;
- remove `assets/bdxadsdk.jar`;
- preserve a backup outside the Apktool tree;
- refuse unknown target fingerprints unless the operator explicitly uses `--force`;
- report remaining SDK references instead of pretending they are gone.

## Dynamic validation plan

Use a disposable test account and isolated network:

1. Capture DNS and destination IPs from first launch through camera viewing.
2. Compare official and patched builds using the same test device and sequence.
3. Hook `Application.onCreate`, `TTAdSdk.init`, `AppLog.init` and `RewardSDK.init` to confirm zero calls.
4. Verify pairing, live view, PTZ, talk-back, SD playback and push notifications.
5. Inspect TLS validation and plaintext fallbacks without intercepting third-party devices.
6. Record crashes, Android verifier errors and missing-class faults.
7. Only then remove residual SDK packages and manifest components in batches.

## Success criteria

The patch is not considered complete until:

- the application starts without advertising SDK initialization;
- core camera functions pass smoke tests;
- no advertising/reward destinations appear in the controlled trace;
- package removal does not introduce runtime verifier failures;
- rebuild and signing steps are reproducible from documented inputs.

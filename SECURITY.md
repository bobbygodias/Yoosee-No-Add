# Security Policy

## Supported scope

The current patch targets the analyzed Yoosee 6.32.3 decompiled layout and its known `ThirdPointsMgrApiImpl.smali` fingerprint. Other releases are unsupported unless separately audited.

## Reporting

Open a GitHub issue for:

- a patcher failure on the supported fingerprint;
- a remaining advertising or reward initialization path;
- a reproducible build or signing defect;
- a privacy-relevant network endpoint with a sanitized trace;
- an Android verifier or runtime crash caused by this patch.

Do not publish camera credentials, private video/audio, household identifiers, signing keys, access tokens or exploit instructions that could be used against third-party devices. Redact packet captures before attaching them.

## Project posture

This repository is defensive research. It does not provide vendor keys, authentication bypasses, persistence mechanisms or access to devices the tester does not own or have explicit permission to assess.

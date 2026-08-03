# Roadmap

## v0.1 — Minimal host-entry neutralization

- [x] Identify ByteDance AppLog initialization.
- [x] Identify Pangle `TTAdSdk` initialization.
- [x] Identify Pangrowth/LuckyCat reward flow.
- [x] Neutralize seven host entry methods.
- [x] Remove `assets/bdxadsdk.jar`.
- [x] Publish a version-gated patcher and synthetic tests.
- [ ] Rebuild and install on an isolated test device.

## v0.2 — Manifest and resource pruning

- [ ] Inventory advertising activities, services, providers and receivers.
- [ ] Remove only components proven unreachable after v0.1.
- [ ] Remove reward/points layouts, strings and drawables in small batches.
- [ ] Rebuild after every batch to identify verifier and resource-table dependencies.

## v0.3 — Physical SDK removal

- [ ] Map all references to ByteDance AppLog, Pangle, Pangrowth, LuckyCat and `bdxadsdk`.
- [ ] Replace required interfaces with minimal local stubs where host signatures demand them.
- [ ] Delete residual SDK packages once reference count reaches zero.
- [ ] Confirm no dynamic class-loading strings recreate the dependency.

## v0.4 — Runtime privacy validation

- [ ] Produce official-versus-patched startup traces.
- [ ] Compare DNS, TLS endpoints and process initialization calls.
- [ ] Verify no advertising/reward traffic remains.
- [ ] Test camera pairing, live video, PTZ, audio, playback and notifications.

## v1.0 — Reproducible hardened build

- [ ] Pin toolchain versions.
- [ ] Publish deterministic patch metadata and checksums.
- [ ] Document known-good device/Android combinations.
- [ ] Publish a signed release only if licensing and redistribution rights are clear.

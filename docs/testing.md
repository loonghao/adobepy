# Testing Strategy

The project uses layered tests so day-to-day checks stay fast while release
checks still cover the broker, generated Python facade, bridge bundles, and
package layout.

## Local Commands

```powershell
npm run test:quick
```

Fast contract gate for most changes. It type-checks bridge sources, validates
IR, runs Python coverage, and runs Rust workspace tests. Use this before every
commit.

```powershell
npm run test:bridges
```

Bridge gate. It builds UXP and CEP bundles, then exercises them against mocked
Photoshop, InDesign, Premiere, After Effects, Illustrator, CSInterface,
WebSocket, and UXP Developer Tool protocol surfaces.

```powershell
npm run test:all
```

Full local gate. It runs the quick gate plus bridge protocol tests. It is the
default acceptance command before publishing.

```powershell
npm run lint
```

Quality gate. It runs Python syntax and architecture checks, TypeScript
type-checking, Rust formatting, and Rust clippy.

```powershell
npm run architecture:check
```

Architecture gate. It checks shared/host import direction, host package parity,
`py.typed` markers, bridge-core neutrality, and camelCase-to-snake_case facade
alias pairs.

```powershell
npm run api:sources:validate
```

Offline source-registry gate. It ensures every IR host has a tracked Adobe API
reference entry before facade coverage expands.

```powershell
npm run test:replay
```

Fixture replay gate. It executes small Python facade examples against recorded
broker responses so user-facing snippets become regression tests.

```powershell
vx just package
```

Release gate. It runs full verification by default, builds the Rust CLI and
bridge bundles, creates the Python wheel, stages the distribution tree, writes
the manifest, creates the archive, and writes the SHA256 file.

## Coverage Layers

- IR contract tests: validate every `generators/ir/*.json` contract and generated
  `.pyi` output before facade or bridge code relies on it.
- API source tests: validate the Adobe reference registry used to expand API
  coverage and aliases.
- Architecture tests: enforce shared/host ownership boundaries and alias parity
  so the facade stays extensible as new Adobe APIs are added.
- Lint/quality gates: compile Python 3.8-compatible sources, type-check bridge
  TypeScript, and run Rust format/clippy checks in CI.
- Python facade tests: assert JS-shaped aliases and Pythonic aliases call the
  same broker methods, including modal and timeout options.
- Replay fixture tests: turn common Python examples into deterministic broker
  call traces.
- Broker tests: assert auth, capability gating, request id restoration, timeout,
  disconnect cleanup, and HTTP endpoint behavior.
- Bridge protocol tests: run bundled bridge JavaScript in Node VM contexts with
  mocked host modules and WebSocket transport, without requiring Adobe apps in
  CI.
- Packaging tests: use the package script as the final artifact smoke because it
  catches missing dist files, bridge templates, wheel metadata, and CLI build
  regressions.

## Next High-Value Additions

- Golden capability snapshots: serialize each bridge `hello.capabilities` payload
  and compare it to the matching IR file so a bridge cannot advertise methods the
  Python facade does not expose.
- Broader fixture replay tests: add traces for save/export, modal operations,
  Premiere project access, and CEP `evalExtendScript` flows.
- Live-host smoke tests: keep them optional and narrow. A self-hosted runner with
  Photoshop and UXP Developer Tool can load the plugin, start the broker, execute
  one read-only script, and export logs. CI should stay green without desktop
  Adobe apps.
- Official API drift checks: periodically crawl or vendor official UXP/DOM type
  metadata from `generators/api_sources/adobe_api_sources.json` and diff
  generated facade names against the current IR. Treat drift as a review signal,
  not an automatic breaking change.
- Wasm build smoke: once `vx` provides the wasm build provider here, add a small
  canary package that compiles, loads through the bridge bundle, and returns a
  deterministic value from Node VM tests.

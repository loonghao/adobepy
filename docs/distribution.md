# Distribution Packaging

Use `vx just package` to build a redistributable archive for the current
platform.

The Python package supports Python 3.8 and newer. The current wheel is pure
Python (`py3-none-any`), so it is already ABI-independent. If a future release
adds a native Python extension for the broker or protocol layer, that extension
must be built with a stable CPython ABI floor of `abi3-py38` instead of
per-minor-version wheels.

```powershell
vx just package
```

For faster local iteration:

```powershell
vx just package-quick
```

The package script:

- installs Node dependencies with `npm ci` if `node_modules` is missing;
- ensures Python build/test helpers `coverage`, `setuptools`, and `wheel` exist;
- runs `npm run test:all` unless `-SkipTests` is passed;
- builds `adobepy` with `cargo build --release -p adobepy-cli --bin adobepy`;
- builds UXP and CEP bridge bundles;
- builds a Python wheel;
- stages the CLI, Python SDK, bridge templates, IR contracts, lockfiles, docs,
  installer, and manifest;
- writes a `.zip` archive and `.sha256` checksum under `dist/`.

After extracting the archive:

```powershell
.\install.ps1 -Python python -AddToUserPath
adobepy doctor
```

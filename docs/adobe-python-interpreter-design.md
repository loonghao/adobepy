# adobepy Design

The interpreter is a sidecar architecture:

- Rust owns CLI, standalone-runtime discovery, broker, sessions, and packaging.
- Python exposes typed facade modules and raw escape hatches.
- Adobe host code stays inside official UXP, CEP/ExtendScript, Lua, Acrobat JS,
  or native plugin runtimes.

The project is the shared Adobe communication layer for DCC MCP adapters. Host
adapters should depend on the stable broker protocol, capability negotiation,
and Python facade contracts instead of carrying independent WebSocket protocol
forks.

First-class MVP hosts are Photoshop, InDesign, and Premiere through UXP. Legacy
MVP hosts are After Effects and Illustrator through CEP + ExtendScript.

## Runtime Contracts

- Python clients send JSON-RPC 2.0 requests to the broker over HTTP or WebSocket.
- Bridges authenticate with the broker token, register a host/target pair, and
  advertise capabilities before receiving requests.
- The broker is the contract gate: it validates session existence, namespace and
  method capabilities, timeout budgets, and request/response correlation.
- Bridges return JSON-RPC responses or typed error codes. Unsupported methods use
  `-32601`; host runtime failures use `-32004`.

## Host Coverage

- Photoshop UXP: `app.getVersion`, active document/layer inspection,
  `action.batchPlay`, document save/export through Photoshop `saveAs`, and raw
  UXP JavaScript evaluation.
- InDesign UXP: `app.getVersion`, active document inspection, and raw UXP
  JavaScript evaluation through the InDesign DOM module.
- Premiere UXP: `app.getVersion`, active project inspection through the Premiere
  UXP project API, and raw UXP JavaScript evaluation.
- After Effects and Illustrator CEP: ExtendScript dispatchers expose app,
  project/document, and raw ExtendScript calls.

## Verification

`npm run test:all` is the acceptance gate. It type-checks bridge code, builds
and tests CEP/UXP bundles against mocked host runtimes, validates IR contracts,
runs Python SDK tests with coverage, and runs the Rust workspace tests.

# Architecture Boundaries

`adobepy` is a shared Adobe communication layer. New host support should extend
the protocol and host adapters without copying transport code or leaking
Photoshop-specific assumptions into shared modules.

## Ownership

| Area | Owns | Must not own |
| --- | --- | --- |
| `crates/adobepy-protocol` | Wire types, host identifiers, JSON-RPC errors, capability contracts | Broker state, HTTP/WebSocket runtime, host DOM behavior |
| `crates/adobepy-broker` | Local HTTP/WebSocket broker, auth, session routing, timeout and capability checks | Photoshop/InDesign/Premiere DOM logic |
| `python/adobe/core` | Broker client, base session, capability normalization, shared errors | Host-specific facade imports |
| `python/adobe/raw` | Explicit raw JavaScript/ExtendScript escape hatches | Typed host facade behavior |
| `python/adobe/dcc_mcp` | Optional DCC MCP skill-result compatibility helpers and adobepy error mapping | MCP server lifecycle or host-specific behavior |
| `python/adobe/<host>` | Python facade and Pythonic aliases for one Adobe host | Sibling host facades or transport implementation |
| `bridges/uxp/core` | Generic UXP bridge transport and protocol handling | Host-specific UXP module names or DOM dispatch |
| `bridges/cep/core` | Generic CEP/WebSocket transport and ExtendScript dispatch wrapper | After Effects or Illustrator business logic |
| `bridges/*/<host>/src/host.ts` | Host adapter, host capabilities, DOM serialization | Broker routing, Python naming conventions |
| `generators/ir` | Host capability shape and facade generation input | Runtime bridge state |

## Method Addition Flow

1. Add or update the host method in `generators/ir/<host>-mvp.json`.
2. Add the official API source or note in
   `generators/api_sources/adobe_api_sources.json` if the method comes from a
   new documentation surface.
3. Implement the host bridge dispatch in the host adapter only.
4. Add the Python facade member with both JavaScript-shaped and Pythonic names
   when the Adobe API uses camelCase.
5. Add a Python facade test or replay fixture that proves both aliases call the
   same broker method.
6. Run `npm run test:quick`; use `npm run test:all` before publishing.

## Review Checklist

- Shared modules do not import host packages.
- Host packages do not import sibling host packages.
- Bridge core code has no host-specific names.
- UXP hosts prefer typed DOM calls before raw eval or `batchPlay`.
- CEP hosts keep `evalExtendScript` separated from typed facade methods.
- Raw payloads are only used at `adobe.raw` or clearly marked escape hatches.
- DCC MCP helpers remain optional and do not make `dcc-mcp-core` a runtime
  dependency of adobepy.
- Broad host errors are converted to protocol error objects with useful
  diagnostics.
- Every camelCase facade member has a snake_case Pythonic sibling.
- Every supported host has IR, API source metadata, Python facade package, and
  `py.typed`.

## Automated Gate

```powershell
npm run architecture:check
```

The gate checks host/package parity, `py.typed` markers, import direction,
camelCase-to-snake_case alias pairs, and bridge-core host neutrality. It is part
of `npm run test:quick`.

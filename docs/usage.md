# adobepy Usage

## Broker

```powershell
adobepy broker --token dev-token
```

The broker listens on `127.0.0.1:47391` and exposes `/health`,
`/v1/capabilities`, `/v1/rpc`, and bridge/client WebSocket routes. Authenticated
routes use `x-adobepy-token`.

## Python

```powershell
$env:ADOBEPY_TOKEN = "dev-token"
python -c "from adobe.photoshop import Photoshop; print(Photoshop(token='dev-token').version)"
```

Photoshop exposes JS-shaped aliases such as `activeDocument`,
`executeAsModal()`, and `action.batchPlay()`, plus Pythonic aliases such as
`active_document` and `batch_play()`.

The MVP facade modules are `adobe.photoshop`, `adobe.indesign`,
`adobe.premiere`, `adobe.after_effects`, and `adobe.illustrator`. Legacy CEP
hosts expose typed convenience properties for version/current project or
document, plus raw ExtendScript through `adobe.raw`.

## Bridges

```powershell
adobepy install-bridge photoshop --dest C:\Temp\adobepy-photoshop-bridge --token dev-token
```

UXP templates cover Photoshop, InDesign, and Premiere. CEP templates cover After
Effects and Illustrator. Host-specific loading, signing, and marketplace flows
remain Adobe workflows.

The UXP manifests allow the default local broker WebSocket endpoints on
`127.0.0.1:47391` and `localhost:47391`. If you run the broker on a different
port or host, update the bridge manifest's `requiredPermissions.network.domains`
before loading the plugin.

export interface CepConfig {
  host: string;
  brokerUrl: string;
  token: string;
  target: string;
  capabilities: {
    host: string;
    bridgeKind: "cep";
    bridgeVersion: string;
    namespaces: string[];
    features: string[];
    methods: Record<string, string[]>;
  };
}

declare const WebSocket: any;
declare const CSInterface: any;

export function startCepBridge(config: CepConfig): void {
  const socket = new WebSocket(config.brokerUrl);
  const cs = new CSInterface();
  socket.addEventListener("open", () => {
    socket.send(JSON.stringify({ type: "hello", token: config.token, target: config.target, capabilities: config.capabilities }));
    console.log("adobepy CEP bridge connected", config.capabilities);
  });
  socket.addEventListener("message", (event: { data: string }) => {
    const message = JSON.parse(event.data);
    if (message.type !== "request") return;
    const request = message.request;
    const encoded = encodeURIComponent(JSON.stringify(request)).replace(/'/g, "%27");
    try {
      cs.evalScript(`adobepyDispatch(decodeURIComponent('${encoded}'))`, (raw: string) => {
        try {
          const parsed = raw ? JSON.parse(raw) : { jsonrpc: "2.0", id: request.id, result: null };
          if (parsed.error) {
            socket.send(JSON.stringify({ type: "error", error: { ...parsed, id: parsed.id ?? request.id } }));
            return;
          }
          if (!Object.prototype.hasOwnProperty.call(parsed, "result")) parsed.result = null;
          socket.send(JSON.stringify({ type: "response", response: parsed }));
        } catch (error: any) {
          socket.send(JSON.stringify({ type: "error", error: hostScriptError(request.id, error) }));
        }
      });
    } catch (error: any) {
      socket.send(JSON.stringify({ type: "error", error: hostScriptError(request.id, error) }));
    }
  });
}

function hostScriptError(id: string | number, error: any) {
  return { jsonrpc: "2.0", id, error: { code: -32004, message: error?.message || String(error) } };
}

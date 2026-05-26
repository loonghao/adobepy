export interface RpcRequest {
  jsonrpc: "2.0";
  id: string | number;
  host: string;
  target?: string;
  namespace: string;
  method: string;
  args?: unknown[];
  options?: Record<string, unknown>;
}

export interface Capabilities {
  host: string;
  bridgeKind: "uxp";
  bridgeVersion: string;
  hostVersion?: string;
  namespaces: string[];
  features: string[];
  methods: Record<string, string[]>;
}

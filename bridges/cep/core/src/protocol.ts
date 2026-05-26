export type BridgeKind = "uxp" | "cep" | "extendscript" | "lua" | "native" | "acrobat-js" | "rest";

export const JSONRPC_VERSION = "2.0" as const;
export const DEFAULT_TARGET = "default" as const;

export const ERROR_CODES = Object.freeze({
  ERROR_PARSE: -32700,
  ERROR_INVALID_REQUEST: -32600,
  ERROR_METHOD_NOT_FOUND: -32601,
  ERROR_HOST_NOT_RUNNING: -32001,
  ERROR_BRIDGE_NOT_INSTALLED: -32002,
  ERROR_CAPABILITY: -32003,
  ERROR_HOST_SCRIPT: -32004,
  ERROR_PERMISSION: -32005,
  ERROR_MODAL_REQUIRED: -32006,
  ERROR_TIMEOUT: -32007,
  ERROR_SERIALIZATION: -32008,
  ERROR_UNAUTHORIZED: -32009,
} as const);

export interface RpcOptions {
  modal?: boolean;
  commandName?: string;
  timeoutMs?: number;
  traceId?: string;
}

export interface RpcRequest {
  jsonrpc: "2.0";
  id: string | number;
  host: string;
  target?: string;
  namespace: string;
  method: string;
  args?: unknown[];
  options?: RpcOptions;
}

export interface RpcResponse {
  jsonrpc: "2.0";
  id: string | number;
  result: unknown;
  diagnostics?: Diagnostics;
}

export interface RpcErrorObject {
  code: number;
  message: string;
  data?: unknown;
}

export interface RpcErrorResponse {
  jsonrpc: "2.0";
  id?: string | number;
  error: RpcErrorObject;
  diagnostics?: Diagnostics;
}

export interface Diagnostics {
  hostVersion?: string;
  bridge?: string;
  durationMs?: number;
  traceId?: string;
}

export interface Capabilities {
  host: string;
  bridgeKind: BridgeKind;
  bridgeVersion: string;
  hostVersion?: string;
  namespaces: string[];
  features: string[];
  methods: Record<string, string[]>;
}

export interface BridgeSessionInfo {
  target: string;
  capabilities: Capabilities;
  connectedAtEpochMs: number;
}

export interface BridgeHello {
  type: "hello";
  token: string;
  target?: string;
  capabilities: Capabilities;
}

export interface BridgeResponse {
  type: "response";
  response: RpcResponse;
}

export interface BridgeError {
  type: "error";
  error: RpcErrorResponse;
}

export interface BridgeRequest {
  type: "request";
  request: RpcRequest;
}

export type BridgeInbound = BridgeHello | BridgeResponse | BridgeError;
export type BridgeOutbound = BridgeRequest;

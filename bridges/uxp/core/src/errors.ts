export const ERROR_METHOD_NOT_FOUND = -32601;
export const ERROR_HOST_SCRIPT = -32004;

export class BridgeRpcError extends Error {
  readonly code: number;
  readonly data?: unknown;

  constructor(code: number, message: string, data?: unknown) {
    super(message);
    this.name = "BridgeRpcError";
    this.code = code;
    this.data = data;
  }
}

export function methodNotFound(namespace: string, method: string): never {
  throw new BridgeRpcError(ERROR_METHOD_NOT_FOUND, `unsupported method ${namespace}.${method}`);
}

export function unavailable(feature: string): never {
  throw new BridgeRpcError(ERROR_HOST_SCRIPT, `${feature} is unavailable in this host runtime`);
}

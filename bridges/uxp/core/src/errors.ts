import { ERROR_CODES } from "./protocol";

export const ERROR_METHOD_NOT_FOUND = ERROR_CODES.ERROR_METHOD_NOT_FOUND;
export const ERROR_HOST_SCRIPT = ERROR_CODES.ERROR_HOST_SCRIPT;

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

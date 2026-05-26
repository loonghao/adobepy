import type { Capabilities, RpcRequest } from "./protocol";

export interface HostAdapter {
  capabilities(): Capabilities;
  dispatch(request: RpcRequest): Promise<unknown>;
}

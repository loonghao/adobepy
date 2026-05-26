#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");

function arg(name, fallback = undefined) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

async function connect(port) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/socket/cli`);
    const clients = [];
    ws.on("message", (raw) => {
      const message = JSON.parse(String(raw));
      if (message.command === "didAddRuntimeClient") clients.push(message);
      if (message.command === "didCompleteConnection") {
        if (!clients[0]) reject(new Error("UXP Developer Tools did not report a connected Adobe host app"));
        else resolve({ ws, client: clients[0] });
      }
    });
    ws.on("error", reject);
  });
}

async function proxy(ws, clientId, message) {
  return new Promise((resolve) => {
    const requestId = `req_${Date.now()}_${Math.random()}`;
    const listener = (raw) => {
      const reply = JSON.parse(String(raw));
      if (reply.command === "reply" && reply.requestId === requestId) {
        ws.off("message", listener);
        resolve(reply);
      }
    };
    ws.on("message", listener);
    ws.send(JSON.stringify({ command: "proxy", clientId, requestId, message }));
  });
}

async function main() {
  const command = process.argv[2];
  if (command !== "load" && command !== "validate") {
    console.log("uxpdt mock helper supports load/validate");
    return;
  }
  const manifestPath = path.resolve(process.argv[3]);
  const port = Number(arg("--port", "5247"));
  const app = arg("--app", "PS");
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const { ws, client } = await connect(port);
  const provider = { type: "disk", path: path.dirname(manifestPath) };
  const validate = await proxy(ws, client.id, { command: "Plugin", action: "validate", params: { provider }, manifest });
  if (validate.error) throw new Error(validate.error);
  if (command === "load") {
    const load = await proxy(ws, client.id, { command: "Plugin", action: "load", params: { provider }, manifest });
    if (load.error) throw new Error(load.error);
    console.log(`loaded ${manifest.name || "Adobe Python Bridge for Photoshop"} for ${app}`);
  } else {
    console.log(`validated ${manifest.name || manifest.id}`);
  }
  ws.close();
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});

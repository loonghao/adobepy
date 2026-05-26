#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const WebSocket = require("ws");

const root = path.resolve(__dirname, "..");
const manifestPath = path.join(root, "bridges", "uxp", "photoshop", "manifest.json");

function runCli(args, port) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [path.join(root, "scripts", "uxpdt.js"), ...args, "--port", String(port)], { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

async function withMockUdt(test) {
  const requests = [];
  const server = new WebSocket.Server({ host: "127.0.0.1", port: 0 });
  await new Promise((resolve) => server.once("listening", resolve));
  const port = server.address().port;
  server.on("connection", (socket) => {
    socket.send(JSON.stringify({ command: "didAddRuntimeClient", id: 42, app: { appId: "PS", appName: "Adobe Photoshop", appVersion: "26.5.0" } }));
    socket.send(JSON.stringify({ command: "didCompleteConnection" }));
    socket.on("message", (raw) => {
      const message = JSON.parse(String(raw));
      requests.push(message);
      assert.strictEqual(message.command, "proxy");
      assert.strictEqual(message.clientId, 42);
      if (message.message.action === "validate") {
        assert.strictEqual(message.message.params.provider.path, path.dirname(manifestPath));
        socket.send(JSON.stringify({ command: "reply", requestId: message.requestId, success: true }));
      } else if (message.message.action === "load") {
        socket.send(JSON.stringify({ command: "reply", requestId: message.requestId, pluginSessionId: "mock-session-1", success: true }));
      }
    });
  });
  try {
    await test(port, requests);
  } finally {
    server.close();
    await new Promise((resolve) => server.once("close", resolve));
  }
}

async function main() {
  assert.ok(fs.existsSync(manifestPath));
  await withMockUdt(async (port, requests) => {
    const result = await runCli(["load", manifestPath, "--app", "PS"], port);
    assert.strictEqual(result.code, 0, `${result.stdout}\n${result.stderr}`);
    assert.match(result.stdout, /loaded Adobe Python Bridge for Photoshop/);
    assert.strictEqual(requests.length, 2);
  });
  console.log("uxpdt mock protocol test passed");
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});

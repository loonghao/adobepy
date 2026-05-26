#!/usr/bin/env node
"use strict";

const esbuild = require("esbuild");
const path = require("path");

const root = path.resolve(__dirname, "..");
const targets = {
  photoshop: { entry: "bridges/uxp/photoshop/src/main.ts", outfile: "bridges/uxp/photoshop/dist/main.js", external: ["photoshop", "uxp"] },
  indesign: { entry: "bridges/uxp/indesign/src/main.ts", outfile: "bridges/uxp/indesign/dist/main.js", external: ["indesign"] },
  premiere: { entry: "bridges/uxp/premiere/src/main.ts", outfile: "bridges/uxp/premiere/dist/main.js", external: ["premierepro"] },
};

async function buildTarget(name) {
  const target = targets[name];
  if (!target) throw new Error(`unknown UXP target: ${name}`);
  await esbuild.build({
    entryPoints: [path.join(root, target.entry)],
    outfile: path.join(root, target.outfile),
    bundle: true,
    platform: "neutral",
    format: "iife",
    target: "es2020",
    external: target.external,
    sourcemap: true,
    logLevel: "silent",
  });
  console.log(`built ${name}: ${target.outfile}`);
}

async function main() {
  const requested = process.argv[2] || "all";
  const names = requested === "all" ? Object.keys(targets) : [requested];
  for (const name of names) await buildTarget(name);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});

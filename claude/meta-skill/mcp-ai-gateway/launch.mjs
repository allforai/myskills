#!/usr/bin/env node
// Entry point for the ai-gateway MCP server.
//
// A plugin upgrade lands in a fresh directory: dist/ is committed, node_modules is not.
// Started directly, the server died on its first import and the tools were simply absent
// until someone ran `/setup update` by hand — after every upgrade. This installs the
// runtime dependencies when they are missing, then starts the server.
//
// stdout belongs to the MCP protocol, so npm's output goes to stderr.
// deferred: no lock around the install, two sessions starting at the same moment in one
// fresh directory produce a corrupted node_modules
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

if (!existsSync(join(root, "node_modules", "@modelcontextprotocol", "sdk"))) {
  console.error("ai-gateway: runtime dependencies are missing; installing them once (npm install --omit=dev)");
  const npm = spawnSync("npm", ["install", "--omit=dev", "--no-audit", "--no-fund"], {
    cwd: root,
    stdio: ["ignore", process.stderr, process.stderr],
    shell: process.platform === "win32",
  });
  if (npm.error || npm.status !== 0) {
    console.error(
      `ai-gateway: could not install dependencies (${npm.error ? npm.error.message : `npm exited ${npm.status}`}). ` +
        `Run \`npm install\` in ${root}; the gateway tools stay unavailable until then.`,
    );
    process.exit(1);
  }
}

await import("./dist/index.js");

/**
 * MCP server: chatgpt-image
 * File-based interaction model for long-running batch tasks.
 * start_batch → spawns detached runner.js → returns immediately
 * check_progress → reads .job.json + .log.txt → returns status
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { readFileSync, existsSync, readdirSync } from "fs";
import { join } from "path";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { runSetupChecks } from "./setup.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RUNNER = join(__dirname, "runner.js");

// ─── MCP Server Setup ─────────────────────────────────────────────────────

const server = new Server(
  { name: "image-batch", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "check_setup",
      description: "Verify all prerequisites before running a batch: macOS, Chrome running, Accessibility permission, chatgpt.com open, logged in.",
      inputSchema: { type: "object", properties: {} }
    },
    {
      name: "start_batch",
      description: "Start a batch image generation job in the background. Returns immediately — use check_progress to monitor.",
      inputSchema: {
        type: "object",
        properties: {
          prompts_file: {
            type: "string",
            description: "Path to JSON file: { outputDir, categories: { name: [prompt, ...] } }"
          }
        },
        required: ["prompts_file"]
      }
    },
    {
      name: "check_progress",
      description: "Read current status of a batch job from its output directory.",
      inputSchema: {
        type: "object",
        properties: {
          output_dir: { type: "string", description: "outputDir from the prompts file" },
          tail_lines: { type: "number", description: "How many recent log lines to return (default: 20)" }
        },
        required: ["output_dir"]
      }
    },
    {
      name: "stop_batch",
      description: "Kill a running batch job.",
      inputSchema: {
        type: "object",
        properties: {
          output_dir: { type: "string", description: "outputDir from the prompts file" }
        },
        required: ["output_dir"]
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "check_setup")    return handleCheckSetup();
  if (name === "start_batch")    return handleStartBatch(args.prompts_file);
  if (name === "check_progress") return handleCheckProgress(args.output_dir, args.tail_lines ?? 20);
  if (name === "stop_batch")     return handleStopBatch(args.output_dir);

  return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
});

// ─── Tool Handlers ─────────────────────────────────────────────────────────

async function handleCheckSetup() {
  const { ok, checks } = await runSetupChecks();
  const lines = checks.map(c => {
    const icon = c.ok ? "✓" : "✗";
    const line = `${icon} ${c.name}: ${c.message}`;
    return c.fix ? `${line}\n    → Fix: ${c.fix}` : line;
  });
  lines.unshift(ok ? "All checks passed — ready to run batches." : "Setup incomplete:");
  return { content: [{ type: "text", text: lines.join("\n") }] };
}

function handleStartBatch(promptsFile) {
  if (!existsSync(promptsFile)) {
    return { content: [{ type: "text", text: `File not found: ${promptsFile}` }], isError: true };
  }

  let config;
  try {
    config = JSON.parse(readFileSync(promptsFile, "utf8"));
  } catch (e) {
    return { content: [{ type: "text", text: `Cannot parse ${promptsFile}: ${e.message}` }], isError: true };
  }

  if (!config.outputDir || typeof config.categories !== "object") {
    return { content: [{ type: "text", text: "Invalid prompts file: needs outputDir + categories" }], isError: true };
  }

  const total = Object.values(config.categories).reduce((s, a) => s + a.length, 0);

  // Spawn detached — MCP server does not wait for it
  const child = spawn(process.execPath, [RUNNER, promptsFile], {
    detached: true,
    stdio: "ignore"
  });
  child.unref();

  return {
    content: [{
      type: "text",
      text: [
        `Batch started (pid: ${child.pid})`,
        `Prompts file: ${promptsFile}`,
        `Output dir:   ${config.outputDir}`,
        `Total:        ${total} prompts`,
        ``,
        `Monitor with: check_progress("${config.outputDir}")`,
        `Log file:     ${config.outputDir}/.log.txt`,
      ].join("\n")
    }]
  };
}

function handleCheckProgress(outputDir, tailLines = 20) {
  const jobFile      = join(outputDir, ".job.json");
  const logFile      = join(outputDir, ".log.txt");
  const progressFile = join(outputDir, ".progress.json");

  if (!existsSync(jobFile)) {
    return { content: [{ type: "text", text: `No job found in ${outputDir}. Run start_batch first.` }] };
  }

  const job      = JSON.parse(readFileSync(jobFile, "utf8"));
  const progress = existsSync(progressFile)
    ? JSON.parse(readFileSync(progressFile, "utf8"))
    : {};
  const doneCount = Object.keys(progress).length;

  // Per-category counts from actual files
  const catLines = [];
  if (existsSync(outputDir)) {
    for (const entry of readdirSync(outputDir)) {
      const catDir = join(outputDir, entry);
      try {
        const files = readdirSync(catDir).filter(f => /\.(png|jpg|webp)$/i.test(f));
        if (files.length) catLines.push(`  ${entry}: ${files.length} images`);
      } catch {}
    }
  }

  // Tail of log file
  let logTail = "";
  if (existsSync(logFile)) {
    const lines = readFileSync(logFile, "utf8").split("\n").filter(Boolean);
    logTail = lines.slice(-tailLines).join("\n");
  }

  // Is process still alive?
  let alive = false;
  if (job.pid && job.status === "running") {
    try { process.kill(job.pid, 0); alive = true; } catch {}
  }

  const statusLine = job.status === "done"
    ? `DONE  (finished: ${job.finishedAt})`
    : alive
      ? `RUNNING (pid: ${job.pid}, started: ${job.startedAt})`
      : `STOPPED (pid: ${job.pid} not found)`;

  const lines = [
    `Status:     ${statusLine}`,
    `Total:      ${job.total ?? "?"}`,
    `Downloaded: ${job.downloaded ?? doneCount}`,
    `Skipped:    ${job.skipped ?? 0}`,
    "",
    "Per category:",
    catLines.length ? catLines.join("\n") : "  (none yet)",
    "",
    `--- last ${tailLines} log lines ---`,
    logTail || "(no log yet)"
  ];

  return { content: [{ type: "text", text: lines.join("\n") }] };
}

function handleStopBatch(outputDir) {
  const jobFile = join(outputDir, ".job.json");
  if (!existsSync(jobFile)) {
    return { content: [{ type: "text", text: `No job found in ${outputDir}` }] };
  }

  const job = JSON.parse(readFileSync(jobFile, "utf8"));
  if (!job.pid) {
    return { content: [{ type: "text", text: "No PID in job file" }] };
  }

  try {
    process.kill(job.pid, "SIGTERM");
    return { content: [{ type: "text", text: `Sent SIGTERM to pid ${job.pid}` }] };
  } catch (e) {
    return { content: [{ type: "text", text: `Could not kill pid ${job.pid}: ${e.message}` }] };
  }
}

// ─── Start ────────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);

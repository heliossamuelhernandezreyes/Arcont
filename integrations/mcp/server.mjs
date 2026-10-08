#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createServer as createNodeHttpServer } from "node:http";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

import { McpServer, createMcpHandler } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import { toNodeHandler } from "@modelcontextprotocol/node";
import * as z from "zod/v4";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ARCONT_ROOT = path.resolve(HERE, "../..");
const SERVER_VERSION = "0.1.0";
const MAX_BRIDGE_STDOUT = 32 * 1024 * 1024;
const MAX_BRIDGE_STDERR = 2 * 1024 * 1024;
const DEFAULT_TIMEOUT_MS = 900_000;

function fail(message) {
  throw new Error(message);
}

function parseCli(argv) {
  const config = {
    project: null,
    transport: "stdio",
    allowProjectWrite: false,
    host: "127.0.0.1",
    port: 8765,
    tokenEnv: "ARCONT_MCP_TOKEN",
    allowedHosts: [],
    python: process.env.PYTHON_BIN || "python3"
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const value = () => {
      if (i + 1 >= argv.length) fail(`missing value for ${arg}`);
      i += 1;
      return argv[i];
    };
    if (arg === "--project") config.project = value();
    else if (arg === "--transport") config.transport = value();
    else if (arg === "--allow-project-write") config.allowProjectWrite = true;
    else if (arg === "--host") config.host = value();
    else if (arg === "--port") config.port = Number(value());
    else if (arg === "--token-env") config.tokenEnv = value();
    else if (arg === "--allowed-host") config.allowedHosts.push(value().toLowerCase());
    else if (arg === "--python") config.python = value();
    else if (arg === "--help") {
      process.stderr.write(
        "Usage: node server.mjs --project PATH [--transport stdio|http] [--allow-project-write] " +
        "[--host HOST] [--port PORT] [--token-env ENV] [--allowed-host HOST] [--python BIN]\n"
      );
      process.exit(0);
    } else fail(`unknown argument: ${arg}`);
  }
  if (!config.project) fail("--project is required");
  if (!["stdio", "http"].includes(config.transport)) fail("--transport must be stdio or http");
  if (!Number.isInteger(config.port) || config.port < 0 || config.port > 65535) fail("--port must be in [0,65535]");
  if (!config.tokenEnv || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(config.tokenEnv)) fail("--token-env must be an environment variable name");

  config.project = fs.realpathSync(path.resolve(config.project));
  const stat = fs.statSync(config.project);
  if (!stat.isDirectory()) fail("--project must resolve to a directory");
  const relative = path.relative(ARCONT_ROOT, config.project);
  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    fail("project must be external to ARCONT");
  }
  return config;
}

function isLoopbackHost(host) {
  const normalized = host.toLowerCase().replace(/^\[|\]$/g, "");
  return normalized === "127.0.0.1" || normalized === "::1" || normalized === "localhost";
}

function normalizedHostHeader(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  try {
    return new URL(`http://${value}`).hostname.toLowerCase().replace(/^\[|\]$/g, "");
  } catch {
    return null;
  }
}

function allowedHttpHosts(config) {
  const hosts = new Set(config.allowedHosts.map(x => x.toLowerCase().replace(/^\[|\]$/g, "")));
  if (isLoopbackHost(config.host)) {
    hosts.add("localhost");
    hosts.add("127.0.0.1");
    hosts.add("::1");
  } else if (!["0.0.0.0", "::"].includes(config.host)) {
    hosts.add(config.host.toLowerCase().replace(/^\[|\]$/g, ""));
  }
  return hosts;
}

function validateHttpExposure(config) {
  const token = process.env[config.tokenEnv] || "";
  const hosts = allowedHttpHosts(config);
  if (!isLoopbackHost(config.host)) {
    if (!token) fail(`non-loopback HTTP requires a bearer token in ${config.tokenEnv}`);
    if (hosts.size === 0) fail("non-loopback wildcard bind requires at least one --allowed-host");
  }
  return { token, hosts };
}

function boundedAppend(current, chunk, limit, label, child) {
  const next = current + chunk.toString("utf8");
  if (Buffer.byteLength(next, "utf8") > limit) {
    child.kill("SIGKILL");
    throw new Error(`${label} exceeded output limit`);
  }
  return next;
}

function runBridge(config, operation, args = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  return new Promise((resolve, reject) => {
    const request = {
      protocol: "arcont-bridge",
      version: 1,
      request_id: `mcp-${process.pid}-${Date.now()}-${runBridge.counter++}`,
      operation,
      arguments: args
    };
    const commandArgs = [
      path.join(ARCONT_ROOT, "tools/arcont_bridge.py"),
      "--project",
      config.project,
      "--request",
      "-"
    ];
    if (config.allowProjectWrite) commandArgs.push("--allow-project-write");
    const child = spawn(config.python, commandArgs, {
      cwd: ARCONT_ROOT,
      stdio: ["pipe", "pipe", "pipe"],
      shell: false,
      env: { ...process.env, PYTHONUNBUFFERED: "1" }
    });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) {
        child.kill("SIGKILL");
        settled = true;
        reject(new Error(`ARCONT bridge timed out after ${timeoutMs} ms`));
      }
    }, timeoutMs);

    child.stdout.on("data", chunk => {
      if (settled) return;
      try {
        stdout = boundedAppend(stdout, chunk, MAX_BRIDGE_STDOUT, "ARCONT bridge stdout", child);
      } catch (error) {
        settled = true;
        clearTimeout(timer);
        reject(error);
      }
    });
    child.stderr.on("data", chunk => {
      if (settled) return;
      try {
        stderr = boundedAppend(stderr, chunk, MAX_BRIDGE_STDERR, "ARCONT bridge stderr", child);
      } catch (error) {
        settled = true;
        clearTimeout(timer);
        reject(error);
      }
    });
    child.on("error", error => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", code => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      let parsed;
      try {
        parsed = JSON.parse(stdout);
      } catch {
        reject(new Error(`ARCONT bridge returned invalid JSON (exit ${code}): ${stderr.slice(-2000)}`));
        return;
      }
      if (code !== 0 && parsed?.ok !== false) {
        parsed = {
          ok: false,
          error: `ARCONT bridge exited with code ${code}`,
          bridge_result: parsed
        };
      }
      resolve(parsed);
    });
    child.stdin.end(JSON.stringify(request));
  });
}
runBridge.counter = 1;

function mcpResult(value) {
  const text = JSON.stringify(value, null, 2);
  return {
    content: [{ type: "text", text }],
    ...(value?.ok === false ? { isError: true } : {})
  };
}

async function mcpCall(config, operation, args = {}) {
  try {
    return mcpResult(await runBridge(config, operation, args));
  } catch (error) {
    return {
      content: [{ type: "text", text: JSON.stringify({ ok: false, error: String(error?.message || error) }, null, 2) }],
      isError: true
    };
  }
}

function buildMcpServer(config) {
  const authority = config.allowProjectWrite ? "read-write" : "read-only";
  const server = new McpServer(
    { name: "arcont", version: SERVER_VERSION },
    {
      capabilities: { tools: {}, resources: {} },
      instructions:
        "ARCONT is a bounded game-development control plane. Call arcont_discover first, inspect project context, " +
        "then use Development Sessions for long-running work. Execute one bounded plan at a time. " +
        `This server instance is ${authority}; tools cannot increase that authority.`
    }
  );

  server.registerTool(
    "arcont_discover",
    {
      title: "Discover ARCONT",
      description:
        "Discover the ARCONT Universal Bridge, capability registry, supported operations and mutation boundary for this project.",
      inputSchema: z.object({})
    },
    async () => mcpCall(config, "discover", {})
  );

  server.registerTool(
    "arcont_project_context",
    {
      title: "Read ARCONT project context",
      description:
        "Read a bounded context bundle: project intent, structural project inspection, local assets, authoring documents, and Development Session capabilities.",
      inputSchema: z.object({
        max_files: z.number().int().min(1).max(200000).default(5000),
        max_assets: z.number().int().min(1).max(10000).default(500)
      })
    },
    async ({ max_files, max_assets }) => {
      const operations = [
        ["project.intent.read", {}],
        ["project.inspect", { max_files }],
        ["assets.inspect", { max_assets }],
        ["authoring.catalog", {}],
        ["development.session.capabilities", {}]
      ];
      const result = { ok: true, project: config.project, authority, context: {} };
      for (const [operation, args] of operations) {
        const value = await runBridge(config, operation, args);
        result.context[operation] = value;
        if (value?.ok === false) result.ok = false;
      }
      return mcpResult(result);
    }
  );

  server.registerTool(
    "arcont_call",
    {
      title: "Call ARCONT Universal Bridge",
      description:
        "Call one Universal Bridge operation discovered by arcont_discover. The MCP server startup authority is the hard ceiling; this tool cannot grant project-write permission.",
      inputSchema: z.object({
        operation: z.string().min(1).max(128),
        arguments: z.record(z.string(), z.unknown()).default({})
      })
    },
    async ({ operation, arguments: args }) => mcpCall(config, operation, args)
  );

  server.registerTool(
    "arcont_session_create",
    {
      title: "Create ARCONT Development Session",
      description:
        "Create a persistent bounded Development Session with milestones, capability allowlist and budgets. Requires server startup with --allow-project-write.",
      inputSchema: z.object({
        spec: z.record(z.string(), z.unknown())
      })
    },
    async ({ spec }) => mcpCall(config, "development.session.create", { spec })
  );

  server.registerTool(
    "arcont_session_inspect",
    {
      title: "Inspect ARCONT Development Session",
      description:
        "Inspect persisted session state, current milestone, budgets, environment pins and any unresolved pending-run crash journal.",
      inputSchema: z.object({
        session_id: z.string().regex(/^[a-z][a-z0-9_-]{0,63}$/)
      })
    },
    async ({ session_id }) => mcpCall(config, "development.session.inspect", { session_id })
  );

  server.registerTool(
    "arcont_session_execute",
    {
      title: "Execute one ARCONT Development Session plan",
      description:
        "Execute exactly one bounded arcont-agent-plan against the active milestone using an exact session revision. Milestone completion requires criterion-to-step evidence.",
      inputSchema: z.object({
        session_id: z.string().regex(/^[a-z][a-z0-9_-]{0,63}$/),
        if_session_revision: z.string().regex(/^[0-9a-f]{64}$/),
        milestone_id: z.string().regex(/^[a-z][a-z0-9_-]{0,63}$/),
        plan: z.record(z.string(), z.unknown()),
        complete_milestone: z.boolean(),
        completion_note: z.string().max(2000).nullable().optional(),
        completion_evidence: z.array(
          z.object({
            criterion_index: z.number().int().min(0).max(15),
            step_ids: z.array(z.string().regex(/^[a-z][a-z0-9_-]{0,63}$/)).min(1).max(8)
          })
        ).max(16).optional()
      })
    },
    async ({
      session_id,
      if_session_revision,
      milestone_id,
      plan,
      complete_milestone,
      completion_note,
      completion_evidence
    }) => {
      const args = {
        session_id,
        if_session_revision,
        milestone_id,
        plan,
        complete_milestone
      };
      if (completion_note !== undefined) args.completion_note = completion_note;
      if (completion_evidence !== undefined) args.completion_evidence = completion_evidence;
      return mcpCall(config, "development.session.execute", args);
    }
  );

  server.registerResource(
    "arcont-project-intent",
    "arcont://project/intent",
    {
      title: "ARCONT project intent",
      description: "Persistent product intent for the external game project.",
      mimeType: "application/json"
    },
    async uri => {
      const value = await runBridge(config, "project.intent.read", {});
      return { contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(value, null, 2) }] };
    }
  );

  server.registerResource(
    "arcont-discovery",
    "arcont://project/discovery",
    {
      title: "ARCONT capability discovery",
      description: "Universal Bridge and capability discovery snapshot.",
      mimeType: "application/json"
    },
    async uri => {
      const value = await runBridge(config, "discover", {});
      return { contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(value, null, 2) }] };
    }
  );

  return server;
}

async function serveHttp(config) {
  const exposure = validateHttpExposure(config);
  const handler = createMcpHandler(() => buildMcpServer(config));
  const nodeHandler = toNodeHandler(handler);
  const allowed = exposure.hosts;

  const httpServer = createNodeHttpServer(async (req, res) => {
    try {
      const base = `http://${req.headers.host || "invalid"}`;
      const url = new URL(req.url || "/", base);
      if (url.pathname !== "/mcp") {
        res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
        res.end("Not Found");
        return;
      }

      const host = normalizedHostHeader(req.headers.host);
      if (!host || !allowed.has(host)) {
        res.writeHead(403, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: "Host header rejected" }));
        return;
      }

      const origin = req.headers.origin;
      if (origin) {
        let originHost = null;
        try {
          originHost = new URL(origin).hostname.toLowerCase().replace(/^\[|\]$/g, "");
        } catch {
          originHost = null;
        }
        if (!originHost || !allowed.has(originHost)) {
          res.writeHead(403, { "content-type": "application/json" });
          res.end(JSON.stringify({ error: "Origin rejected" }));
          return;
        }
      }

      if (exposure.token) {
        const authorization = req.headers.authorization || "";
        if (authorization !== `Bearer ${exposure.token}`) {
          res.writeHead(401, {
            "content-type": "application/json",
            "www-authenticate": 'Bearer realm="arcont-mcp"'
          });
          res.end(JSON.stringify({ error: "Bearer token required" }));
          return;
        }
      }

      await nodeHandler(req, res);
    } catch (error) {
      if (!res.headersSent) res.writeHead(500, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "MCP HTTP gateway failure" }));
      process.stderr.write(`ARCONT MCP HTTP error: ${String(error?.stack || error)}\n`);
    }
  });

  await new Promise((resolve, reject) => {
    httpServer.once("error", reject);
    httpServer.listen(config.port, config.host, resolve);
  });

  const address = httpServer.address();
  const port = typeof address === "object" && address ? address.port : config.port;
  const visibleHost = isLoopbackHost(config.host) ? "127.0.0.1" : config.host;
  process.stderr.write(
    `ARCONT_MCP_HTTP ${JSON.stringify({
      url: `http://${visibleHost}:${port}/mcp`,
      authority: config.allowProjectWrite ? "read-write" : "read-only",
      token_required: Boolean(exposure.token)
    })}\n`
  );

  const close = async () => {
    await handler.close();
    await new Promise(resolve => httpServer.close(resolve));
  };
  process.once("SIGTERM", () => void close().finally(() => process.exit(0)));
  process.once("SIGINT", () => void close().finally(() => process.exit(0)));
}

async function main() {
  const config = parseCli(process.argv.slice(2));
  if (config.transport === "stdio") {
    process.stderr.write(
      `ARCONT MCP stdio ready (${config.allowProjectWrite ? "read-write" : "read-only"}) for ${config.project}\n`
    );
    serveStdio(() => buildMcpServer(config));
    return;
  }
  await serveHttp(config);
}

main().catch(error => {
  process.stderr.write(`ARCONT MCP fatal: ${String(error?.stack || error)}\n`);
  process.exit(1);
});

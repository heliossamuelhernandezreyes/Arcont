#!/usr/bin/env node
import { Client, StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { spawn } from "node:child_process";
import { request as httpRequest } from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.join(HERE, "server.mjs");

function parseArgs(argv) {
  const out = { project: null, evidence: null };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--project") out.project = argv[++i];
    else if (argv[i] === "--evidence") out.evidence = argv[++i];
    else throw new Error(`unknown argument: ${argv[i]}`);
  }
  if (!out.project || !out.evidence) throw new Error("--project and --evidence are required");
  out.project = path.resolve(out.project);
  out.evidence = path.resolve(out.evidence);
  return out;
}

function toolJson(result) {
  const text = result?.content?.find?.(item => item?.type === "text")?.text;
  if (typeof text !== "string") throw new Error("tool result has no text JSON block");
  return JSON.parse(text);
}

function findNested(value, predicate, depth = 0) {
  if (depth > 12 || value === null || value === undefined) return null;
  if (typeof value === "object" && predicate(value)) return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const found = findNested(item, predicate, depth + 1);
      if (found) return found;
    }
  } else if (typeof value === "object") {
    for (const item of Object.values(value)) {
      const found = findNested(item, predicate, depth + 1);
      if (found) return found;
    }
  }
  return null;
}

function findSession(value) {
  return findNested(
    value,
    item =>
      typeof item === "object" &&
      typeof item?.id === "string" &&
      typeof item?.revision === "string" &&
      Array.isArray(item?.milestones) &&
      item?.protocol === "arcont-development-session"
  );
}

function modernClient(name) {
  return new Client(
    { name, version: "1.0.0" },
    { versionNegotiation: { mode: { pin: "2026-07-28" } } }
  );
}

async function connectStdio(project, allowWrite, name) {
  const client = modernClient(name);
  const args = [SERVER, "--project", project, "--transport", "stdio"];
  if (allowWrite) args.push("--allow-project-write");
  const transport = new StdioClientTransport({ command: process.execPath, args });
  await client.connect(transport);
  if (client.getProtocolEra() !== "modern") throw new Error("stdio did not negotiate modern MCP era");
  return { client, transport };
}

async function waitForHttpServer(child, timeoutMs = 20_000) {
  return await new Promise((resolve, reject) => {
    let buffer = "";
    const timer = setTimeout(() => reject(new Error("HTTP MCP server startup timed out")), timeoutMs);
    child.stderr.on("data", chunk => {
      buffer += chunk.toString("utf8");
      for (const line of buffer.split("\n")) {
        if (!line.startsWith("ARCONT_MCP_HTTP ")) continue;
        clearTimeout(timer);
        try {
          resolve(JSON.parse(line.slice("ARCONT_MCP_HTTP ".length)));
        } catch (error) {
          reject(error);
        }
        return;
      }
      buffer = buffer.slice(Math.max(0, buffer.lastIndexOf("\n") + 1));
    });
    child.once("exit", code => {
      clearTimeout(timer);
      reject(new Error(`HTTP MCP server exited early with code ${code}`));
    });
    child.once("error", error => {
      clearTimeout(timer);
      reject(error);
    });
  });
}

function rawStatus(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req = httpRequest(
      {
        hostname: parsed.hostname,
        port: parsed.port,
        path: parsed.pathname,
        method: "POST",
        headers: {
          "content-type": "application/json",
          "content-length": "2",
          ...headers
        }
      },
      res => {
        res.resume();
        res.on("end", () => resolve(res.statusCode));
      }
    );
    req.on("error", reject);
    req.end("{}");
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  fs.mkdirSync(args.project, { recursive: true });
  fs.mkdirSync(args.evidence, { recursive: true });

  const assertions = {};
  const evidence = {};

  // 1. Read-only authority cannot bootstrap a project.
  {
    const { client } = await connectStdio(args.project, false, "arcont-readonly-acceptance");
    try {
      const tools = await client.listTools();
      const names = tools.tools.map(tool => tool.name).sort();
      evidence.readonly_tools = names;
      for (const expected of [
        "arcont_discover",
        "arcont_project_context",
        "arcont_call",
        "arcont_session_create",
        "arcont_session_inspect",
        "arcont_session_execute"
      ]) {
        if (!names.includes(expected)) throw new Error(`missing MCP tool: ${expected}`);
      }
      assertions.mcp_tools_discoverable = true;

      const discoverCall = await client.callTool({ name: "arcont_discover", arguments: {} });
      const discover = toolJson(discoverCall);
      evidence.discover = discover;
      if (discover?.ok !== true) throw new Error("arcont_discover failed");
      assertions.universal_bridge_discovered = true;

      const refused = await client.callTool({
        name: "arcont_call",
        arguments: {
          operation: "project.bootstrap",
          arguments: {
            template: "godot-3d-minimal",
            intent: {
              protocol: "arcont-project-intent",
              version: 1,
              project_id: "mcp_acceptance",
              title: "MCP Acceptance",
              genre: "third-person action",
              targets: ["Windows"],
              asset_policy: {
                user_assets: true,
                public_assets: false,
                commercial_use_required: true,
                allow_network_discovery: false
              }
            }
          }
        }
      });
      evidence.readonly_write_attempt = toolJson(refused);
      if (refused.isError !== true) throw new Error("read-only MCP server allowed project bootstrap");
      assertions.readonly_server_cannot_escalate = true;
    } finally {
      await client.close();
    }
  }

  // 2. Writable authority bootstraps, opens a session, and completes a real milestone.
  {
    const { client } = await connectStdio(args.project, true, "arcont-writable-acceptance");
    try {
      const bootstrapCall = await client.callTool({
        name: "arcont_call",
        arguments: {
          operation: "project.bootstrap",
          arguments: {
            template: "godot-3d-minimal",
            intent: {
              protocol: "arcont-project-intent",
              version: 1,
              project_id: "mcp_acceptance",
              title: "MCP Acceptance",
              genre: "third-person action",
              targets: ["Windows"],
              goals: ["Prove a current MCP client can drive ARCONT through a persistent development session."],
              priorities: ["movement", "evidence", "bounded execution"],
              asset_policy: {
                user_assets: true,
                public_assets: false,
                commercial_use_required: true,
                allow_network_discovery: false
              }
            }
          }
        }
      });
      evidence.bootstrap = toolJson(bootstrapCall);
      if (bootstrapCall.isError) throw new Error("writable MCP bootstrap failed");
      assertions.mcp_bootstrapped_external_project = true;

      const contextCall = await client.callTool({
        name: "arcont_project_context",
        arguments: { max_files: 2000, max_assets: 100 }
      });
      evidence.context = toolJson(contextCall);
      if (contextCall.isError) throw new Error("project context tool failed");
      assertions.project_context_available = true;

      const createCall = await client.callTool({
        name: "arcont_session_create",
        arguments: {
          spec: {
            id: "mcp_build",
            goal: "Create and verify a minimal player movement scaffold through MCP.",
            capability_allowlist: ["godot.structured.control"],
            permissions: { project_write: true },
            budgets: {
              max_plan_runs: 3,
              max_execution_steps: 16,
              max_write_steps: 10,
              max_failed_runs: 1
            },
            milestones: [
              {
                id: "movement",
                goal: "Create move_forward input, a Player script and attach Player to the main scene.",
                acceptance: [
                  "The move_forward input action is written through Godot.",
                  "A valid CharacterBody3D Player script is attached to Player in the main scene."
                ]
              }
            ]
          }
        }
      });
      const created = toolJson(createCall);
      evidence.session_create = created;
      if (createCall.isError) throw new Error("MCP session create failed");
      const createdSession = findSession(created);
      if (!createdSession) throw new Error("could not locate created development session");
      assertions.development_session_created = true;

      const playerSource = `extends CharacterBody3D

@export var speed: float = 4.0

func _physics_process(_delta):
    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    velocity = Vector3(input_vector.x, 0.0, input_vector.y) * speed
    move_and_slide()
`;

      const plan = {
        protocol: "arcont-agent-plan",
        version: 1,
        id: "mcp_movement",
        goal: "Create a bounded forward input and Player movement scaffold.",
        permissions: { project_write: true },
        capability_allowlist: ["godot.structured.control"],
        steps: [
          {
            id: "validate",
            kind: "invoke",
            capability: "godot.structured.control",
            request: { protocol_version: 1, operation: "validate" },
            expect: [{ pointer: "/result/ok", op: "equals", value: true }]
          },
          {
            id: "forward",
            kind: "invoke",
            capability: "godot.structured.control",
            request: {
              protocol_version: 1,
              operation: "input.action.set",
              if_revision: { $from: "validate", pointer: "/result/result/project_revision" },
              action: "move_forward",
              deadzone: 0.2,
              events: [{ type: "key", keycode: "W", physical: true }]
            }
          },
          {
            id: "script",
            kind: "invoke",
            capability: "godot.structured.control",
            request: {
              protocol_version: 1,
              operation: "script.create",
              path: "scripts/player.gd",
              if_revision: null,
              source: playerSource
            },
            expect: [{ pointer: "/result/result/revision", op: "exists" }]
          },
          {
            id: "scene_before",
            kind: "invoke",
            capability: "godot.structured.control",
            request: {
              protocol_version: 1,
              operation: "scene.inspect",
              scene: "scenes/main.tscn"
            },
            expect: [{ pointer: "/result/result/revision", op: "exists" }]
          },
          {
            id: "scene_edit",
            kind: "invoke",
            capability: "godot.structured.control",
            request: {
              protocol_version: 1,
              operation: "scene.edit",
              scene: "scenes/main.tscn",
              if_revision: { $from: "scene_before", pointer: "/result/result/revision" },
              changes: [
                { op: "add", parent: ".", name: "Player", type: "CharacterBody3D" },
                { op: "attach_script", path: "Player", script: "res://scripts/player.gd" }
              ]
            },
            expect: [{ pointer: "/result/result/revision", op: "exists" }]
          }
        ]
      };

      const executeCall = await client.callTool({
        name: "arcont_session_execute",
        arguments: {
          session_id: "mcp_build",
          if_session_revision: createdSession.revision,
          milestone_id: "movement",
          plan,
          complete_milestone: true,
          completion_note: "MCP-driven plan completed with machine-backed acceptance evidence.",
          completion_evidence: [
            { criterion_index: 0, step_ids: ["forward"] },
            { criterion_index: 1, step_ids: ["script", "scene_edit"] }
          ]
        }
      });
      const executed = toolJson(executeCall);
      evidence.session_execute = executed;
      if (executeCall.isError) throw new Error("MCP session execute failed");
      const completedSession = findSession(executed);
      if (!completedSession || completedSession.status !== "completed") {
        throw new Error("MCP-driven development session did not complete");
      }
      if (completedSession.milestones?.[0]?.completion_evidence?.length !== 2) {
        throw new Error("MCP milestone completion evidence was not persisted");
      }
      assertions.mcp_executed_bounded_session_plan = true;
      assertions.mcp_completion_evidence_persisted = true;

      const inspectCall = await client.callTool({
        name: "arcont_session_inspect",
        arguments: { session_id: "mcp_build" }
      });
      const inspected = toolJson(inspectCall);
      evidence.session_inspect_stdio = inspected;
      const inspectedSession = findSession(inspected);
      if (!inspectedSession || inspectedSession.revision !== completedSession.revision) {
        throw new Error("MCP session inspect did not return persisted final revision");
      }
      assertions.stdio_persisted_session_reinspectable = true;
    } finally {
      await client.close();
    }
  }

  // 3. Serve the same project over current Streamable HTTP with auth and Host protection.
  {
    const token = "arcont-mcp-acceptance-token";
    const child = spawn(
      process.execPath,
      [
        SERVER,
        "--project",
        args.project,
        "--transport",
        "http",
        "--host",
        "127.0.0.1",
        "--port",
        "0",
        "--token-env",
        "ARCONT_MCP_TEST_TOKEN"
      ],
      {
        stdio: ["ignore", "ignore", "pipe"],
        env: { ...process.env, ARCONT_MCP_TEST_TOKEN: token }
      }
    );
    try {
      const started = await waitForHttpServer(child);
      evidence.http_server = started;
      if (started.token_required !== true) throw new Error("HTTP MCP server did not enable bearer auth");

      const unauth = await rawStatus(started.url);
      evidence.http_unauthorized_status = unauth;
      if (unauth !== 401) throw new Error(`HTTP MCP unauthenticated request returned ${unauth}`);
      assertions.http_bearer_auth_enforced = true;

      const hostRejected = await rawStatus(started.url, {
        Authorization: `Bearer ${token}`,
        Host: "attacker.invalid"
      });
      evidence.http_bad_host_status = hostRejected;
      if (hostRejected !== 403) throw new Error(`HTTP MCP bad Host returned ${hostRejected}`);
      assertions.http_host_validation_enforced = true;

      const client = modernClient("arcont-http-acceptance");
      const transport = new StreamableHTTPClientTransport(new URL(started.url), {
        requestInit: { headers: { Authorization: `Bearer ${token}` } }
      });
      try {
        await client.connect(transport);
        if (client.getProtocolEra() !== "modern") throw new Error("HTTP did not negotiate modern MCP era");
        assertions.http_modern_2026_protocol = true;

        const tools = await client.listTools();
        if (!tools.tools.some(tool => tool.name === "arcont_session_inspect")) {
          throw new Error("HTTP MCP tool list missing session inspect");
        }
        const inspectCall = await client.callTool({
          name: "arcont_session_inspect",
          arguments: { session_id: "mcp_build" }
        });
        const inspected = toolJson(inspectCall);
        evidence.session_inspect_http = inspected;
        const session = findSession(inspected);
        if (!session || session.status !== "completed") throw new Error("HTTP MCP could not inspect completed session");
        assertions.http_and_stdio_share_same_arcont_state = true;
      } finally {
        await client.close();
      }
    } finally {
      child.kill("SIGTERM");
      await new Promise(resolve => {
        if (child.exitCode !== null) resolve();
        else {
          child.once("exit", resolve);
          setTimeout(() => {
            child.kill("SIGKILL");
            resolve();
          }, 5000).unref();
        }
      });
    }
  }

  const summary = {
    ok: Object.values(assertions).every(Boolean),
    protocol_revision: "2026-07-28",
    sdk: {
      server: "2.3.1",
      client: "2.3.1",
      node: "2.1.1"
    },
    assertions,
    evidence_files: Object.keys(evidence),
    limits: [
      "The MCP gateway exposes the existing Universal Bridge; it does not add a writer primitive.",
      "Project-write authority is fixed when the server process starts and cannot be escalated by a tool call.",
      "The acceptance proves current MCP stdio and Streamable HTTP interoperability on Linux CI; it does not establish compatibility with every proprietary MCP host UI."
    ]
  };
  fs.writeFileSync(path.join(args.evidence, "summary.json"), JSON.stringify(summary, null, 2) + "\n");
  fs.writeFileSync(path.join(args.evidence, "details.json"), JSON.stringify(evidence, null, 2) + "\n");
  process.stdout.write(JSON.stringify(summary, null, 2) + "\n");
  if (!summary.ok) process.exitCode = 1;
}

main().catch(error => {
  process.stderr.write(String(error?.stack || error) + "\n");
  process.exit(1);
});

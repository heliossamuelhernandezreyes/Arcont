# ARCONT MCP Agent Gateway v1

ARCONT MCP Agent Gateway exposes the existing Universal Agent Bridge through
the official Model Context Protocol SDK.

It is an adapter, not a second control plane.

```text
MCP host / AI
      |
      |  MCP 2026-07-28 or compatible 2025-era client
      v
ARCONT MCP Gateway
      |
      |  arcont-bridge JSON request
      v
Universal Agent Bridge
      |
      v
ARCONT capabilities / Development Sessions
      |
      v
external game project
```

The gateway does not add writer primitives and cannot grant itself more
authority than it received when the process started.

## Protocol and SDK

The gateway uses the official MCP TypeScript SDK v2:

- `@modelcontextprotocol/server@2.3.1`
- `@modelcontextprotocol/client@2.3.1` for acceptance tests
- `@modelcontextprotocol/node@2.1.1`
- `zod@4.6.5`

`integrations/mcp/package-lock.json` pins the resolved transitive dependency graph used by CI.

The tested modern protocol revision is `2026-07-28`.

The official SDK entries used here are:

- `serveStdio(factory)` for local stdio hosts;
- `createMcpHandler(factory)` for Streamable HTTP;
- `toNodeHandler(handler)` for Node HTTP adaptation.

The v2 SDK serves the modern 2026 era and its documented 2025-era compatibility
path from the same server factory.

## Tools

The gateway exposes a deliberately small model-facing surface:

### `arcont_discover`

Read the Universal Bridge and capability registry.

An agent should normally call this first.

### `arcont_project_context`

Read a bounded bundle containing:

- persistent project intent;
- project structure;
- local asset inventory;
- authoring catalog;
- Development Session capabilities.

This is a convenience reader. It does not replace individual bridge calls.

### `arcont_call`

Call one Universal Bridge operation.

The tool accepts:

```json
{
  "operation": "project.intent.read",
  "arguments": {}
}
```

It cannot pass a project-write flag. Authority comes only from server startup.

### `arcont_session_create`

Create one persistent bounded Development Session.

Requires a gateway started with `--allow-project-write`.

### `arcont_session_inspect`

Read current session state, milestone, budgets, pins, history and crash journal.

### `arcont_session_execute`

Execute exactly one ordinary `arcont-agent-plan` against the active milestone.

It still requires:

- exact session revision;
- session capability allowlist;
- bounded plan/step/write/failure budgets;
- Development Session single-writer lock;
- intent, registry and toolchain pins;
- pending-run crash journal;
- machine-backed criterion-to-step evidence before milestone completion.

## Resources

The server also exposes:

```text
arcont://project/intent
arcont://project/discovery
```

They are read-only views over the same bridge.

## stdio

Install dependencies once:

```bash
cd integrations/mcp
npm ci --ignore-scripts --no-audit --no-fund
```

Start a read-only server:

```bash
node integrations/mcp/server.mjs \
  --project /absolute/path/to/game \
  --transport stdio
```

Start a server allowed to mutate that external project:

```bash
node integrations/mcp/server.mjs \
  --project /absolute/path/to/game \
  --transport stdio \
  --allow-project-write
```

The flag is a process-level ceiling. A model/tool call cannot enable it later.

## Streamable HTTP

Localhost is the default:

```bash
export ARCONT_MCP_TOKEN='replace-with-a-secret'

node integrations/mcp/server.mjs \
  --project /absolute/path/to/game \
  --transport http \
  --host 127.0.0.1 \
  --port 8765 \
  --token-env ARCONT_MCP_TOKEN
```

Endpoint:

```text
http://127.0.0.1:8765/mcp
```

When the configured token environment variable is populated, every MCP request
requires:

```text
Authorization: Bearer <token>
```

For a non-loopback bind the gateway refuses startup unless:

1. a bearer token is configured; and
2. at least one allowed Host is known.

Wildcard binds such as `0.0.0.0` therefore require explicit
`--allowed-host` entries.

Example:

```bash
export ARCONT_MCP_TOKEN='replace-with-a-secret'

node integrations/mcp/server.mjs \
  --project /absolute/path/to/game \
  --transport http \
  --host 0.0.0.0 \
  --port 8765 \
  --allowed-host arcont.example.internal \
  --token-env ARCONT_MCP_TOKEN
```

HTTP requests are checked for:

- the exact `/mcp` path;
- allowed `Host`;
- allowed `Origin` when Origin is present;
- bearer token when configured.

The gateway deliberately does not implement its own OAuth authorization server.
A production Internet deployment should terminate TLS and identity at a
reviewed reverse proxy or use the official MCP authorization stack rather than
treating this simple bearer gate as a complete identity system.

## Recommended agent workflow

A model should use:

```text
arcont_discover
      |
      v
arcont_project_context
      |
      v
inspect/create Development Session
      |
      v
reason about current milestone
      |
      v
submit ONE bounded plan
      |
      v
read receipt/evidence
      |
      v
inspect session again
      |
      +--> complete -> stop
      |
      +--> active -> reason and submit next bounded plan
      |
      +--> paused/pending-run -> review evidence; never blind-retry
```

The external model owns planning. ARCONT owns the execution envelope.

## Security boundary

MCP Gateway v1 does **not**:

- execute arbitrary shell requested by the model;
- expose a shell tool;
- add a new project writer;
- let a model toggle write authority;
- disable revision checks;
- remove capability allowlists;
- bypass Development Session budgets;
- replay an ambiguous crashed mutation;
- embed a production Godot project in ARCONT;
- claim that successful technical acceptance proves subjective AAA quality.

The Python process launched by the gateway is always
`tools/arcont_bridge.py` with fixed argv construction and `shell=false`.

## Acceptance

`.github/workflows/mcp-agent-gateway-acceptance.yml` uses the official MCP
client package and pins the modern `2026-07-28` era.

It proves:

1. stdio tool discovery;
2. read-only server cannot bootstrap/write;
3. write authority supplied only at process startup;
4. bootstrap of an empty external Godot project through MCP;
5. creation of a persistent Development Session through MCP;
6. execution/completion of a real structured-Godot milestone through MCP;
7. criterion-to-step completion evidence persists;
8. the same session can be re-inspected through stdio;
9. non-loopback HTTP without a bearer token refuses startup;
10. wildcard HTTP bind without an explicit allowed Host refuses startup;
11. Streamable HTTP rejects unauthenticated requests when token auth is enabled;
12. Streamable HTTP rejects a malicious Host header;
13. the official client negotiates the modern 2026 protocol;
14. stdio and HTTP observe the same persisted ARCONT session state.

This is interoperability evidence for the tested SDK/client on Linux CI. It is
not a claim that every proprietary MCP host exposes identical UI or connection
settings.

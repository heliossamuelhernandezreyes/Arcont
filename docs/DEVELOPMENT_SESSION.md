# Development Session v1

A Development Session is ARCONT's persistent orchestration layer for an external
AI agent working on a game over multiple bounded iterations.

It does **not** contain an autonomous model loop. The external AI proposes each
next plan. ARCONT owns the durable state, budgets, milestone order, revision
checks, receipts, capability allowlist and stopping behavior.

This keeps the long-range workflow:

```text
high-level goal
  -> model decomposes milestones
  -> one bounded ARCONT plan
  -> evidence/receipt
  -> inspect session
  -> model decides next bounded plan
  -> ...
```

without turning the project into an unbounded self-modifying loop.

## Bridge operations

```text
development.session.capabilities
development.session.create
development.session.inspect
development.session.execute
```

`capabilities` and `inspect` are pure session reads.

`create` and `execute` write project-local session state and require the
normal Universal Bridge project-write opt-in.

## Creating a session

Example:

```json
{
  "protocol": "arcont-bridge",
  "version": 1,
  "request_id": "start-game-session",
  "operation": "development.session.create",
  "arguments": {
    "spec": {
      "id": "prototype",
      "goal": "Build a playable third-person prototype.",
      "capability_allowlist": [
        "godot.structured.control",
        "public-asset.control"
      ],
      "permissions": {"project_write": true},
      "budgets": {
        "max_plan_runs": 8,
        "max_execution_steps": 64,
        "max_write_steps": 32,
        "max_failed_runs": 3
      },
      "milestones": [
        {
          "id": "movement",
          "goal": "Create player movement and input.",
          "acceptance": [
            "Player script validates in Godot.",
            "Player node is present in the main scene."
          ]
        },
        {
          "id": "environment",
          "goal": "Create a small playable environment.",
          "acceptance": [
            "Environment assets have recorded provenance.",
            "The main scene loads with the environment."
          ]
        }
      ]
    }
  }
}
```

The first milestone becomes `active`; the rest remain `pending`.

## Persistent pins

A session captures:

- SHA-256 of `project.intent.json`;
- SHA-256 of `agent.capabilities.json`;
- a toolchain SHA-256 covering each allowlisted capability entrypoint plus the
  execution/session core;
- session capability allowlist;
- explicit project-write policy;
- milestone order and acceptance prose;
- bounded execution budgets.

If project intent, the ARCONT capability registry, or the pinned capability
implementation toolchain changes, execution stops. V1 requires a new reviewed
session rather than silently migrating an old plan onto changed product
requirements or changed tools.

A session also owns a kernel-backed lock file. Only one execute request can
advance a given session at a time. A second agent therefore cannot race the same
`if_session_revision` and silently overwrite the first agent's state.

## One plan per execute

`development.session.execute` accepts exactly one ordinary
`arcont-agent-plan`.

The plan is still validated and executed by
`tools/agent_execution_loop.py`; Development Session does not implement a
second mutation engine.

Requirements:

- `milestone_id` must be the currently active milestone;
- `if_session_revision` must match the persisted session revision;
- the plan capability allowlist must be a subset of the session allowlist;
- the plan cannot request project write when the session forbids it;
- the whole plan must fit inside remaining plan/step/write budgets.

Example:

```json
{
  "operation": "development.session.execute",
  "arguments": {
    "session_id": "prototype",
    "if_session_revision": "<current session sha256>",
    "milestone_id": "movement",
    "complete_milestone": true,
    "completion_note": "All plan expectations passed.",
    "plan": {
      "protocol": "arcont-agent-plan",
      "version": 1,
      "id": "movement_core",
      "goal": "Create bounded player movement.",
      "permissions": {"project_write": true},
      "capability_allowlist": ["godot.structured.control"],
      "steps": []
    }
  }
}
```

The normal execution-plan schema still requires real steps; the empty array
above is only abbreviated documentation.

## Crash journal and no silent retry

Before ARCONT starts a plan it atomically writes:

```text
.arcont/development-sessions/<session-id>/pending-run.json
```

The marker binds the session revision, run ID, milestone, plan ID and plan
SHA-256 **before any plan mutation occurs**.

If the process dies while the plan is running, or after project files changed
but before the new session state is committed, the marker remains. A later
execute request refuses to repeat the plan automatically. The agent must inspect
the project/evidence and start a reviewed recovery path rather than assuming
the old session revision is safe to replay.

If the process dies only after session state was committed, a later execute may
clear the stale pending marker only when the same run already exists in session
history **and** its persisted receipt still exists with the exact recorded
SHA-256. A missing/corrupt receipt fails closed.

After a normal successful state commit, the pending marker is removed.

If a plan fails:

1. its complete execution result is written to an immutable run receipt;
2. the failed-run counter increases;
3. the milestone remains active;
4. the session returns `review-failure-and-submit-new-plan`;
5. ARCONT does not mutate the plan and does not run it again.

The next attempt requires a new explicit request with the new
`session_revision`.

When the configured failure budget is exhausted, the session moves to
`paused`.

## Budgets

V1 bounds four dimensions:

```text
max_plan_runs        1..32
max_execution_steps  1..256
max_write_steps      0..96
max_failed_runs      0..8
```

Before a plan runs, its total steps and worst-case invoke count must fit the
remaining budget.

After execution, actual completed steps and actual write steps from the normal
execution receipt are charged to the session.

The intent, registry and toolchain pins are checked again after the plan. If
the environment changed while the plan was running, the run is still preserved
as evidence but the milestone is not completed and the session pauses with
`environment-changed-during-run`.

Exhaustion pauses the session instead of automatically extending it.

## Milestone completion

A model may request `complete_milestone=true` only for a milestone that has
explicit acceptance criteria in the session specification.

ARCONT does not pretend to understand acceptance prose semantically. Instead,
`complete_milestone=true` requires a `completion_evidence` mapping with
exactly one entry for every acceptance criterion. Each entry names one or more
steps from the submitted plan.

A cited step counts as machine-backed evidence only when it completed
successfully and either:

- it had machine-readable expectations that were evaluated; or
- it invoked a capability that reports a real project write.

Completion therefore means:

- the submitted bounded plan completed successfully;
- every acceptance criterion is explicitly mapped to successful execution
  evidence from that same plan;
- the environment pins remained stable;
- the caller explicitly requests milestone completion.

The immutable run receipt stores both the requested criterion→step mapping and
the verified per-step evidence result. The milestone persists the checked
evidence, completing run ID and optional completion note.

ARCONT still does not claim that it understands the *meaning* of the prose; the
explicit mapping makes the model's claim auditable instead of accepting a bare
"done".

The next pending milestone becomes active. When the final milestone completes,
the session status becomes `completed`.

## Receipts

State:

```text
.arcont/development-sessions/<session-id>/session.json
```

Each execution creates a receipt under:

```text
.arcont/development-sessions/<session-id>/runs/
```

A history row stores:

- run ID;
- milestone ID;
- plan ID and plan SHA-256;
- receipt path and receipt SHA-256;
- result status;
- completed/write step counts;
- failed step when present.

The session state itself has a canonical SHA-256 revision. Mutating a stale
session revision is refused. Session directories and lock files may not be
symlinks.

## Relationship to the AI

This layer is deliberately provider-neutral.

ChatGPT, Claude, Gemini or a local model can all perform the planning loop:

```text
read intent + inspect session
       ↓
reason about active milestone
       ↓
propose one ARCONT plan
       ↓
session.execute
       ↓
read receipt/evidence
       ↓
decide the next plan
```

The model may be creative in planning. Execution remains deterministic,
bounded and auditable.

## V1 limits

Development Session v1 does not:

- call an LLM itself;
- retry failed plans automatically;
- increase its own budgets;
- change the capability registry;
- migrate automatically when project intent changes;
- run multiple plans in one request;
- claim subjective visual/AAA quality from technical acceptance;
- run forever in the background.

Those boundaries are intentional.

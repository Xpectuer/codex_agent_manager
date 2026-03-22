---
name: "codex-agent-manager"
description: "Manage Codex agent role files under CODEX_HOME/agents. Use when adding, validating, listing, updating, or removing per-agent TOML configs for roles such as default, worker, or explorer, especially when a candidate .toml must pass syntax and semantic checks before activation."
---

# Codex Agent Manager

Manage per-agent TOML files under `$CODEX_HOME/agents` with a strict validate-then-apply workflow.

## Quick start

- Read [references/agent-files.md](references/agent-files.md) when you need the expected role-file shape or the validation rules.
- Use `scripts/manage_agent.py template <role>` to create a safe starter file.
- Edit the candidate TOML outside `$CODEX_HOME/agents` first.
- Run `scripts/manage_agent.py validate --source <candidate.toml>`.
- Run `scripts/manage_agent.py install --source <candidate.toml>` only after validation passes.

## Workflow

### Add or update an agent

1. Create a candidate file:

```bash
python3 scripts/manage_agent.py template worker > /tmp/worker.toml
```

2. Edit the candidate TOML with the desired role settings.

3. Validate syntax and semantics:

```bash
python3 scripts/manage_agent.py validate --source /tmp/worker.toml
```

4. Install into `$CODEX_HOME/agents`:

```bash
python3 scripts/manage_agent.py install --source /tmp/worker.toml
```

`install` re-runs validation, creates `$CODEX_HOME/agents` if needed, and writes only after all checks pass.

### Remove an agent

Use:

```bash
python3 scripts/manage_agent.py remove worker
```

The script removes the active file by moving it into `$CODEX_HOME/agents/.removed/` with a collision-proof timestamped backup name.

### Inspect active agents

Use:

```bash
python3 scripts/manage_agent.py list
```

This prints each valid active role file with its filename, parsed role, and description. Invalid role files are reported as warnings on stderr and do not block the rest of the listing.

## Validation rules

- Require TOML syntax to parse successfully.
- Require the role name to be inferred from the filename stem and match lowercase hyphen-case.
- Require `description` to be present and non-empty.
- Validate supported field types and enums for common role settings such as `model`, `model_provider`, `approval_policy`, `sandbox_mode`, and reasoning effort.
- Reject global config sections such as `agents`, `projects`, `model_providers`, `profiles`, and `history` in per-agent files.
- Reject unknown top-level keys so invalid role files do not silently drift into `$CODEX_HOME/agents`.
- Keep `list` usable by warning on invalid installed files instead of aborting the whole command.

If a user wants to use a field outside the bundled validator's supported set, inspect [references/agent-files.md](references/agent-files.md) first, then extend `scripts/manage_agent.py` before writing the file.

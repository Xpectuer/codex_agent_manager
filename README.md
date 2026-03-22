# codex-agent-manager

Manage validated Codex agent role files under `$CODEX_HOME/agents`.

This repository packages:

- A Codex skill definition in [SKILL.md](SKILL.md)
- A strict validation and install CLI in [scripts/manage_agent.py](scripts/manage_agent.py)
- A reference note describing the supported per-agent schema in [references/agent-files.md](references/agent-files.md)

The intended workflow is validate first, then install. Role files are drafted outside `$CODEX_HOME/agents`, checked for syntax and supported fields, and only then copied into the active agents directory.

## What It Does

The CLI manages standalone per-role TOML files such as:

- `$CODEX_HOME/agents/default.toml`
- `$CODEX_HOME/agents/worker.toml`
- `$CODEX_HOME/agents/explorer.toml`

Supported operations:

- Generate a safe starter template for a new role
- Validate candidate TOML files before activation
- Install a validated role into `$CODEX_HOME/agents`
- List active installed roles
- Remove a role by moving it into `agents/.removed/`

## Repository Layout

```text
.
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── agent-files.md
└── scripts/
    └── manage_agent.py
```

## Requirements

- Python 3.11 or newer
- A Codex environment that uses `$CODEX_HOME/agents/*.toml` for custom role files

`scripts/manage_agent.py` uses the standard-library `tomllib`, so no third-party dependencies are required.

## Quick Start

Set `CODEX_HOME` if it is not already configured:

```bash
export CODEX_HOME="$HOME/.codex"
```

Create a draft role file:

```bash
python3 scripts/manage_agent.py template worker > /tmp/worker.toml
```

Edit `/tmp/worker.toml`, then validate it:

```bash
python3 scripts/manage_agent.py validate --source /tmp/worker.toml
```

Install it after validation succeeds:

```bash
python3 scripts/manage_agent.py install --source /tmp/worker.toml
```

Inspect active roles:

```bash
python3 scripts/manage_agent.py list
```

Remove a role cleanly:

```bash
python3 scripts/manage_agent.py remove worker
```

## CLI Usage

Show help:

```bash
python3 scripts/manage_agent.py --help
```

Subcommands:

### `template`

Print a starter TOML document for a role name.

```bash
python3 scripts/manage_agent.py template explorer
```

This validates the role name format before printing the template.

### `validate`

Validate a candidate TOML file without writing anything into `$CODEX_HOME`.

```bash
python3 scripts/manage_agent.py validate --source /tmp/explorer.toml
```

This checks:

- The file exists
- The file ends in `.toml`
- The filename stem is a valid role name
- TOML syntax parses successfully
- Required fields are present
- Field types and enum values are valid
- Unsupported or forbidden top-level keys are rejected

### `install`

Validate a candidate TOML file, create `$CODEX_HOME/agents` if needed, and copy the file into place.

```bash
python3 scripts/manage_agent.py install --source /tmp/explorer.toml
```

You can override `CODEX_HOME` per command:

```bash
python3 scripts/manage_agent.py install \
  --source /tmp/explorer.toml \
  --codex-home /tmp/test-codex-home
```

### `list`

List all valid active role files in `$CODEX_HOME/agents`.

```bash
python3 scripts/manage_agent.py list
```

Output format:

```text
<role>    <filename>    <description>
```

Malformed installed files are reported as warnings on stderr and skipped so one bad file does not hide the rest.

### `remove`

Deactivate a role by moving it into `$CODEX_HOME/agents/.removed/` with a timestamped backup name.

```bash
python3 scripts/manage_agent.py remove explorer
```

This is intentionally non-destructive: the active file is moved, not deleted.

## Validation Rules

The validator is intentionally strict. It accepts a narrow set of fields for per-agent role files and rejects everything else.

Required fields:

- `name`
- `description`

Optional fields:

- `nickname_candidates`
- `model`
- `model_provider`
- `model_reasoning_effort`
- `plan_mode_reasoning_effort`
- `approval_policy`
- `sandbox_mode`
- `model_supports_reasoning_summaries`
- `openai_base_url`
- `base_instructions`
- `developer_instructions`

Supported enums:

- `model_reasoning_effort`: `minimal`, `low`, `medium`, `high`, `xhigh`
- `plan_mode_reasoning_effort`: `minimal`, `low`, `medium`, `high`, `xhigh`
- `approval_policy`: `untrusted`, `on-failure`, `on-request`, `never`
- `sandbox_mode`: `read-only`, `workspace-write`, `danger-full-access`

Explicitly rejected global config sections:

- `agents`
- `projects`
- `model_providers`
- `profiles`
- `history`
- `experimental`
- `mcp_servers`

For the full validator scope, see [references/agent-files.md](references/agent-files.md).

## Role Naming Rules

The role name is inferred from the TOML filename stem. For example, `/tmp/research-helper.toml` becomes the role name `research-helper`.

A valid role name:

- Uses lowercase letters, digits, and hyphens only
- Must not start with `-`
- Must not end with `-`
- Must not contain consecutive hyphens
- Must be 64 characters or fewer

## Example Role File

```toml
name = "worker"
description = "Worker role"
model = "gpt-5.4"
model_reasoning_effort = "medium"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
nickname_candidates = ["worker"]
developer_instructions = "You are the worker role. Follow the role description and complete the assigned work pragmatically."
```

## Using This As A Skill Repository

This repo also includes a Codex skill definition:

- [SKILL.md](SKILL.md)
- [agents/openai.yaml](agents/openai.yaml)

The skill is designed to guide an agent through the same safe workflow:

1. Generate a candidate file with `template`
2. Edit the candidate outside `$CODEX_HOME/agents`
3. Run `validate`
4. Run `install` only after validation passes

## Development

Run the CLI directly during development:

```bash
python3 scripts/manage_agent.py --help
```

There is currently no dedicated test suite in this repository, so the primary verification path is exercising the CLI commands against temporary TOML files and a temporary `--codex-home`.

## License

No license file is currently present in this repository.

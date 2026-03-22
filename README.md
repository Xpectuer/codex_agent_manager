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

- installation 

```shell
# assume you installed npm
npx skills add Xpectuer/codex_agent_manager
```


- prompt

```
# in codex 
$codex-agent-manager
  add agents
  - general-purpose [gpt-5.4 medium think effort]
  - coding-expert [gpt-5.4 medium think effort]
  - code reviewer [gpt-5.4 medium think effort]
  - debugger [gpt-5.4 high think effort]
```

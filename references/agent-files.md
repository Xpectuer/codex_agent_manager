# Codex Agent Role Files

This skill manages standalone role files in `$CODEX_HOME/agents/*.toml`.

## What this skill assumes

- The role name comes from the TOML filename stem.
- The file content is a per-agent config layer, not a full global `config.toml`.
- `description` should exist in the role file so the role is self-describing when discovered later.

## Sources used

- `https://linux.do/t/topic/1785189`
- `https://developers.openai.com/codex/config-schema.json`

The `linux.do` post establishes the operational convention that custom agent roles live in an `agents/` directory as separate TOML files. The OpenAI config schema is the reference for config-style fields and enum values.

## Validator scope

The bundled validator is intentionally strict for safety. It accepts the common per-role fields below and rejects everything else.

### Required

- `name`: string
- `description`: string

### Optional scalar fields

- `model`: string
- `model_provider`: string
- `model_reasoning_effort`: `minimal|low|medium|high|xhigh`
- `plan_mode_reasoning_effort`: `minimal|low|medium|high|xhigh`
- `approval_policy`: `untrusted|on-failure|on-request|never`
- `sandbox_mode`: `read-only|workspace-write|danger-full-access`
- `model_supports_reasoning_summaries`: boolean
- `openai_base_url`: string
- `base_instructions`: string
- `developer_instructions`: string

### Optional array fields

- `nickname_candidates`: array of unique non-empty strings

## Explicitly rejected global sections

These belong in the main Codex config, not an individual role file:

- `agents`
- `projects`
- `model_providers`
- `profiles`
- `history`
- `experimental`
- `mcp_servers`

## Operational guidance

- Draft changes outside `$CODEX_HOME/agents`.
- Always run `validate` before `install`.
- Let `install` be the only step that writes into `$CODEX_HOME/agents`.
- Use `remove` to deactivate a role cleanly while keeping a collision-proof timestamped backup.
- Use `list` to inspect valid installed roles; malformed files are reported as warnings and skipped so one bad file does not hide the rest.

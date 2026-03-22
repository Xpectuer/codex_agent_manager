#!/usr/bin/env python3
"""Manage validated Codex agent role files under CODEX_HOME/agents."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import tomllib


ROLE_TEMPLATE = """name = "{role}"
description = "{role} role"
model = "gpt-5.4"
model_reasoning_effort = "medium"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
nickname_candidates = ["{role}"]
developer_instructions = "You are the {role} role. Follow the role description and complete the assigned work pragmatically."
"""

ROLE_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")
FORBIDDEN_TOP_LEVEL_KEYS = {
    "agents",
    "projects",
    "model_providers",
    "profiles",
    "history",
    "experimental",
    "mcp_servers",
}
ALLOWED_KEYS = {
    "name",
    "description",
    "nickname_candidates",
    "model",
    "model_provider",
    "model_reasoning_effort",
    "plan_mode_reasoning_effort",
    "approval_policy",
    "sandbox_mode",
    "model_supports_reasoning_summaries",
    "openai_base_url",
    "base_instructions",
    "developer_instructions",
}
REASONING_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
APPROVAL_POLICIES = {"untrusted", "on-failure", "on-request", "never"}
SANDBOX_MODES = {"read-only", "workspace-write", "danger-full-access"}


@dataclass
class ValidationResult:
    role: str
    source: Path
    data: dict


class ValidationError(Exception):
    """Raised when a candidate role file fails semantic validation."""


def detect_codex_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    raw = os.environ.get("CODEX_HOME")
    if not raw:
        raise ValidationError("CODEX_HOME is not set and --codex-home was not provided.")
    return Path(raw).expanduser().resolve()


def role_name_from_path(path: Path) -> str:
    name = path.stem.strip()
    if not name:
        raise ValidationError(f"Unable to infer role name from {path}.")
    if len(name) > 64:
        raise ValidationError(f"Role name '{name}' is too long; max length is 64.")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        raise ValidationError(
            f"Role name '{name}' must not start/end with '-' or contain consecutive hyphens."
        )
    invalid = [ch for ch in name if ch not in ROLE_NAME_CHARS]
    if invalid:
        chars = "".join(sorted(set(invalid)))
        raise ValidationError(
            f"Role name '{name}' is invalid; unsupported characters: {chars!r}."
        )
    return name


def parse_toml(source: Path) -> dict:
    try:
        return tomllib.loads(source.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"TOML syntax error in {source}: {exc}") from exc


def ensure_string(data: dict, key: str, required: bool = False) -> None:
    value = data.get(key)
    if value is None:
        if required:
            raise ValidationError(f"Missing required string field: {key}")
        return
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Field '{key}' must be a non-empty string.")


def ensure_bool(data: dict, key: str) -> None:
    value = data.get(key)
    if value is None:
        return
    if not isinstance(value, bool):
        raise ValidationError(f"Field '{key}' must be a boolean.")


def ensure_enum(data: dict, key: str, allowed: set[str]) -> None:
    value = data.get(key)
    if value is None:
        return
    if not isinstance(value, str) or value not in allowed:
        ordered = ", ".join(sorted(allowed))
        raise ValidationError(f"Field '{key}' must be one of: {ordered}")


def ensure_nickname_candidates(data: dict) -> None:
    values = data.get("nickname_candidates")
    if values is None:
        return
    if not isinstance(values, list):
        raise ValidationError("Field 'nickname_candidates' must be an array of strings.")
    normalized = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                "Field 'nickname_candidates' must contain only non-empty strings."
            )
        normalized.append(value.strip())
    if len(set(normalized)) != len(normalized):
        raise ValidationError("Field 'nickname_candidates' must not contain duplicates.")


def validate_candidate(source: Path) -> ValidationResult:
    if not source.exists():
        raise ValidationError(f"Source file does not exist: {source}")
    if source.suffix != ".toml":
        raise ValidationError(f"Source file must end with .toml: {source}")

    role = role_name_from_path(source)
    data = parse_toml(source)

    if not isinstance(data, dict):
        raise ValidationError("Parsed TOML root must be a table.")

    unexpected = sorted(set(data) - ALLOWED_KEYS)
    forbidden = [key for key in unexpected if key in FORBIDDEN_TOP_LEVEL_KEYS]
    if forbidden:
        names = ", ".join(forbidden)
        raise ValidationError(
            f"Per-agent role files must not contain global config sections: {names}"
        )
    if unexpected:
        names = ", ".join(unexpected)
        raise ValidationError(f"Unsupported top-level key(s): {names}")

    ensure_string(data, "name", required=True)
    ensure_string(data, "description", required=True)
    ensure_string(data, "model")
    ensure_string(data, "model_provider")
    ensure_string(data, "openai_base_url")
    ensure_string(data, "base_instructions")
    ensure_string(data, "developer_instructions")
    ensure_enum(data, "model_reasoning_effort", REASONING_EFFORTS)
    ensure_enum(data, "plan_mode_reasoning_effort", REASONING_EFFORTS)
    ensure_enum(data, "approval_policy", APPROVAL_POLICIES)
    ensure_enum(data, "sandbox_mode", SANDBOX_MODES)
    ensure_bool(data, "model_supports_reasoning_summaries")
    ensure_nickname_candidates(data)

    return ValidationResult(role=role, source=source, data=data)


def agents_dir(codex_home: Path) -> Path:
    return codex_home / "agents"


def unique_removed_target(removed_dir: Path, role: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = removed_dir / f"{role}.{stamp}.toml"
    counter = 1
    while target.exists():
        target = removed_dir / f"{role}.{stamp}.{counter}.toml"
        counter += 1
    return target


def command_template(args: argparse.Namespace) -> int:
    role = role_name_from_path(Path(f"{args.role}.toml"))
    sys.stdout.write(ROLE_TEMPLATE.format(role=role))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    result = validate_candidate(Path(args.source).expanduser().resolve())
    print(
        f"VALID {result.role}: syntax and semantic checks passed for {result.source}"
    )
    return 0


def command_install(args: argparse.Namespace) -> int:
    result = validate_candidate(Path(args.source).expanduser().resolve())
    codex_home = detect_codex_home(args.codex_home)
    target_dir = agents_dir(codex_home)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{result.role}.toml"
    shutil.copyfile(result.source, target_path)
    print(f"INSTALLED {result.role}: {target_path}")
    return 0


def command_remove(args: argparse.Namespace) -> int:
    codex_home = detect_codex_home(args.codex_home)
    role = role_name_from_path(Path(f"{args.role}.toml"))
    source = agents_dir(codex_home) / f"{role}.toml"
    if not source.exists():
        raise ValidationError(f"Role file does not exist: {source}")

    removed_dir = agents_dir(codex_home) / ".removed"
    removed_dir.mkdir(parents=True, exist_ok=True)
    target = unique_removed_target(removed_dir, role)
    shutil.move(str(source), str(target))
    print(f"REMOVED {role}: moved to {target}")
    return 0


def command_list(args: argparse.Namespace) -> int:
    codex_home = detect_codex_home(args.codex_home)
    target_dir = agents_dir(codex_home)
    if not target_dir.exists():
        print(f"No agents directory at {target_dir}")
        return 0

    files = sorted(path for path in target_dir.glob("*.toml") if path.is_file())
    if not files:
        print(f"No active role files in {target_dir}")
        return 0
    invalid_count = 0
    for path in files:
        try:
            result = validate_candidate(path)
        except ValidationError as exc:
            invalid_count += 1
            print(f"WARN {path.name}: {exc}", file=sys.stderr)
            continue
        description = result.data["description"].strip()
        print(f"{result.role}\t{path.name}\t{description}")
    if invalid_count:
        print(
            f"WARN: skipped {invalid_count} invalid role file(s) in {target_dir}",
            file=sys.stderr,
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage validated Codex agent role files under CODEX_HOME/agents."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser("template", help="Print a starter TOML template.")
    template_parser.add_argument("role", help="Role name to use for the template filename stem.")
    template_parser.set_defaults(func=command_template)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a candidate role TOML file."
    )
    validate_parser.add_argument("--source", required=True, help="Path to candidate .toml file.")
    validate_parser.set_defaults(func=command_validate)

    install_parser = subparsers.add_parser(
        "install", help="Validate then install a role TOML into CODEX_HOME/agents."
    )
    install_parser.add_argument("--source", required=True, help="Path to candidate .toml file.")
    install_parser.add_argument(
        "--codex-home",
        help="Override CODEX_HOME for this command.",
    )
    install_parser.set_defaults(func=command_install)

    remove_parser = subparsers.add_parser(
        "remove", help="Deactivate a role by moving it into agents/.removed/."
    )
    remove_parser.add_argument("role", help="Role name to remove.")
    remove_parser.add_argument(
        "--codex-home",
        help="Override CODEX_HOME for this command.",
    )
    remove_parser.set_defaults(func=command_remove)

    list_parser = subparsers.add_parser(
        "list", help="List active role files in CODEX_HOME/agents."
    )
    list_parser.add_argument(
        "--codex-home",
        help="Override CODEX_HOME for this command.",
    )
    list_parser.set_defaults(func=command_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

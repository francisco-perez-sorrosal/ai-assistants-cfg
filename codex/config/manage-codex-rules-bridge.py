#!/usr/bin/env python3
"""Install/check/uninstall Praxion-managed Codex rules bridge config."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path


PRAXION_HOOK_STATUS_PREFIX = "Praxion:"
STATE_DIR = Path(".codex/praxion")
STATE_FILE = STATE_DIR / "config_state.json"
HOOKS_FILE = Path(".codex/hooks.json")
CONFIG_FILE = Path(".codex/config.toml")


def load_rules_bridge_exporter(repo_root: Path):
    exporter_path = repo_root / "codex" / "config" / "export-codex-rules-bridge.py"
    spec = importlib.util.spec_from_file_location("export_codex_rules_bridge", exporter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load exporter from {exporter_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_expected_hooks(repo_root: Path, project_root: Path) -> dict[str, list[dict]]:
    exporter = load_rules_bridge_exporter(repo_root)
    hooks = exporter.render_hook_registrations()["hooks"]
    project_root_str = project_root.as_posix()
    for groups in hooks.values():
        for group in groups:
            for hook in group.get("hooks", []):
                command = str(hook.get("command", ""))
                hook["command"] = command.replace("__PRAXION_PROJECT_ROOT__", project_root_str)
    return hooks


def is_praxion_managed_group(group: dict) -> bool:
    for hook in group.get("hooks", []):
        status = str(hook.get("statusMessage", ""))
        command = str(hook.get("command", ""))
        if status.startswith(PRAXION_HOOK_STATUS_PREFIX) or "/.codex/hooks/praxion-" in command:
            return True
    return False


def normalize_group(group: dict) -> str:
    return json.dumps(group, sort_keys=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_hooks_json(project_root: Path, expected_hooks: dict[str, list[dict]]) -> None:
    hooks_path = project_root / HOOKS_FILE
    if hooks_path.exists():
        payload = load_json(hooks_path)
    else:
        payload = {"hooks": {}}

    hooks = payload.setdefault("hooks", {})
    for event_name, groups in expected_hooks.items():
        existing_groups = [
            group for group in hooks.get(event_name, []) if not is_praxion_managed_group(group)
        ]
        existing_groups.extend(groups)
        hooks[event_name] = existing_groups

    dump_json(hooks_path, payload)


def uninstall_hooks_json(project_root: Path) -> None:
    hooks_path = project_root / HOOKS_FILE
    if not hooks_path.exists():
        return

    payload = load_json(hooks_path)
    hooks = payload.get("hooks", {})
    cleaned: dict[str, list[dict]] = {}
    for event_name, groups in hooks.items():
        remaining = [group for group in groups if not is_praxion_managed_group(group)]
        if remaining:
            cleaned[event_name] = remaining

    if cleaned:
        payload["hooks"] = cleaned
        dump_json(hooks_path, payload)
    else:
        hooks_path.unlink()


def check_hooks_json(project_root: Path, expected_hooks: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    hooks_path = project_root / HOOKS_FILE
    problems: list[str] = []
    if not hooks_path.exists():
        return False, [f"Codex hooks missing: {hooks_path}"]

    payload = load_json(hooks_path)
    hooks = payload.get("hooks", {})

    for event_name, expected_groups in expected_hooks.items():
        actual_groups = [group for group in hooks.get(event_name, []) if is_praxion_managed_group(group)]
        actual_norm = {normalize_group(group) for group in actual_groups}
        expected_norm = {normalize_group(group) for group in expected_groups}
        missing = expected_norm - actual_norm
        stale = actual_norm - expected_norm
        for _group in missing:
            problems.append(f"Codex hooks missing Praxion registration for {event_name}")
        for _group in stale:
            problems.append(f"Unexpected stale Praxion hook registration for {event_name}")

    extra_events = set(hooks) - set(expected_hooks)
    for event_name in extra_events:
        for group in hooks.get(event_name, []):
            if is_praxion_managed_group(group):
                problems.append(f"Unexpected stale Praxion hook registration for {event_name}")
                break

    return not problems, problems


def load_state(project_root: Path) -> dict | None:
    state_path = project_root / STATE_FILE
    if not state_path.exists():
        return None
    return load_json(state_path)


def save_state(project_root: Path, state: dict) -> None:
    dump_json(project_root / STATE_FILE, state)


def find_features_section(lines: list[str]) -> tuple[int | None, int | None]:
    section_start = None
    section_end = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*\[features\]\s*$", line):
            section_start = index
            section_end = len(lines)
            for later in range(index + 1, len(lines)):
                if re.match(r"^\s*\[[^]]+\]\s*$", lines[later]):
                    section_end = later
                    break
            break
    return section_start, section_end


def find_codex_hooks_line(lines: list[str], start: int, end: int) -> int | None:
    for index in range(start, end):
        if re.match(r"^\s*codex_hooks\s*=\s*(true|false)\s*$", lines[index]):
            return index
    return None


def install_config(project_root: Path) -> None:
    config_path = project_root / CONFIG_FILE
    original_exists = config_path.exists()
    original_text = config_path.read_text(encoding="utf-8") if original_exists else ""
    state = load_state(project_root)
    if state is None:
        lines = original_text.splitlines()
        start, end = find_features_section(lines)
        original_value = None
        if start is not None and end is not None:
            line_index = find_codex_hooks_line(lines, start + 1, end)
            if line_index is not None:
                original_value = "true" in lines[line_index]
        state = {
            "config_original_exists": original_exists,
            "config_original_codex_hooks": original_value,
        }
        save_state(project_root, state)

    lines = original_text.splitlines()
    start, end = find_features_section(lines)
    if start is None or end is None:
        new_text = original_text.rstrip()
        if new_text:
            new_text += "\n\n"
        new_text += "[features]\ncodex_hooks = true\n"
    else:
        line_index = find_codex_hooks_line(lines, start + 1, end)
        if line_index is None:
            lines.insert(start + 1, "codex_hooks = true")
        else:
            lines[line_index] = "codex_hooks = true"
        new_text = "\n".join(lines).rstrip() + "\n"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(new_text, encoding="utf-8")


def uninstall_config(project_root: Path) -> None:
    config_path = project_root / CONFIG_FILE
    state = load_state(project_root)
    if state is None:
        return

    original_exists = state.get("config_original_exists", False)
    original_value = state.get("config_original_codex_hooks", None)

    if config_path.exists():
        lines = config_path.read_text(encoding="utf-8").splitlines()
        start, end = find_features_section(lines)
        if start is not None and end is not None:
            line_index = find_codex_hooks_line(lines, start + 1, end)
            if original_value is None:
                if line_index is not None:
                    del lines[line_index]
                    end -= 1
                feature_has_content = any(lines[index].strip() for index in range(start + 1, end))
                if not feature_has_content:
                    del lines[start:end]
            else:
                restored = "true" if original_value else "false"
                if line_index is None:
                    lines.insert(start + 1, f"codex_hooks = {restored}")
                else:
                    lines[line_index] = f"codex_hooks = {restored}"

        new_text = "\n".join(lines).strip()
        if new_text:
            config_path.write_text(new_text + "\n", encoding="utf-8")
        elif not original_exists:
            config_path.unlink()
        else:
            config_path.write_text("", encoding="utf-8")

    state_path = project_root / STATE_FILE
    if state_path.exists():
        state_path.unlink()
        try:
            state_path.parent.rmdir()
        except OSError:
            pass


def check_config(project_root: Path) -> tuple[bool, list[str]]:
    config_path = project_root / CONFIG_FILE
    if not config_path.exists():
        return False, [f"Codex config missing: {config_path}"]

    lines = config_path.read_text(encoding="utf-8").splitlines()
    start, end = find_features_section(lines)
    if start is None or end is None:
        return False, ["Codex config missing [features] section for codex_hooks"]

    line_index = find_codex_hooks_line(lines, start + 1, end)
    if line_index is None:
        return False, ["Codex config missing codex_hooks = true"]
    if "true" not in lines[line_index]:
        return False, ["Codex config has stale codex_hooks setting"]
    return True, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--mode", choices={"install", "check", "uninstall"}, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    project_root = args.project_root.resolve()
    expected_hooks = load_expected_hooks(repo_root, project_root)

    if args.mode == "install":
        install_config(project_root)
        install_hooks_json(project_root, expected_hooks)
        return 0

    if args.mode == "uninstall":
        uninstall_hooks_json(project_root)
        uninstall_config(project_root)
        return 0

    hooks_ok, hook_problems = check_hooks_json(project_root, expected_hooks)
    config_ok, config_problems = check_config(project_root)
    for problem in [*config_problems, *hook_problems]:
        print(problem)
    return 0 if hooks_ok and config_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

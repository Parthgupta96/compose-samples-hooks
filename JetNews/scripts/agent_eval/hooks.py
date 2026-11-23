"""Claude Code hook handlers. Each reads the hook payload as JSON on stdin.

Per-session state lives in the system temp directory as agent-eval-<session>.<kind>:
    files   paths recorded by --record and kept after a failed Stop
    rounds  failed Stop rounds in the current turn
    marker  empty file whose mtime marks the turn start or the last passing Stop
"""
import json
import os
import re
import sys
import tempfile

from .checks import run_checks
from .common import CODE_SUFFIXES, ROOT, read_text, remove, working_tree_files, write_text

MAX_FIX_ROUNDS = 3
# ponytail: guards Edit|Write only; a Bash command can still write these files. Match Bash
# commands against this list if an agent is seen doing that.
GUARDED_PATHS = (
    ".claude/hooks/",
    ".claude/settings",
    "scripts/agent_eval.py",
    "scripts/agent_eval/",
    "config/agent_eval.json",
    "config/detekt.yml",
    "config/ktlint.editorconfig",
)
# config/recomposition_screens.json is not guarded: an agent maps the tags it adds without asking.
BUILD_FILES = ("build.gradle", "build.gradle.kts")
VERSION_CATALOG = "libs.versions.toml"
DEPENDENCY_LINE = re.compile(
    r"^\s*(implementation|api|compileOnly|runtimeOnly|annotationProcessor|kapt|ksp|lintChecks|coreLibraryDesugaring|"
    r"\w*(Implementation|Api|CompileOnly|RuntimeOnly))\b\s*[(\"']"
)


def session_file(payload, kind="files"):
    """Path of one piece of per-session state.

    Args:
        payload: hook payload; uses session_id.
        kind: "files", "rounds" or "marker".

    Returns:
        Absolute path in the system temp directory.
    """
    session = re.sub(r"\W", "_", str(payload.get("session_id", "unknown")))
    return os.path.join(tempfile.gettempdir(), f"agent-eval-{session}.{kind}")


def read_payload():
    """Reads the hook payload from stdin. Exits 0 on input that is not JSON.

    Returns:
        The payload dict.
    """
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)


def edited_path(payload):
    """Repo-relative path of the file an Edit or Write targets.

    Args:
        payload: hook payload; uses tool_input.file_path.

    Returns:
        The path; it starts with ".." outside the repo, and is empty when the payload has none.
    """
    path = str(payload.get("tool_input", {}).get("file_path", ""))
    return os.path.relpath(os.path.realpath(path), ROOT) if path else ""


def changed_since(marker):
    """Git-changed code files written after the marker. Covers files that a Bash command wrote.

    Args:
        marker: path of the marker file.

    Returns:
        Repo-relative paths; empty when the marker does not exist.
    """
    try:
        since = os.path.getmtime(marker)
    except OSError:
        return []
    recent = []
    for rel in working_tree_files():
        try:
            if os.path.getmtime(os.path.join(ROOT, rel)) > since:
                recent.append(rel)
        except OSError:
            continue
    return recent


def mark_turn():
    """UserPromptSubmit: marks the turn start and resets the fix rounds."""
    payload = read_payload()
    write_text(session_file(payload, "marker"), "")
    remove(session_file(payload, "rounds"))


def added_dependencies(rel, old_text, new_text):
    """Finds the dependency lines an edit adds to a build file or the version catalog.

    Args:
        rel: repo-relative path of the edited file.
        old_text: text the edit replaces (the whole file for a Write).
        new_text: text the edit writes.

    Returns:
        The added lines: dependency declarations in build.gradle(.kts), or any non-comment line in
        libs.versions.toml. Empty for other files.
    """
    added = [line.strip() for line in new_text.splitlines() if line.strip() and line not in old_text.splitlines()]
    if os.path.basename(rel) in BUILD_FILES:
        return [line for line in added if DEPENDENCY_LINE.match(line)]
    if os.path.basename(rel) == VERSION_CATALOG:
        return [line for line in added if not line.startswith("#")]
    return []


def edit_texts(payload, rel):
    """(old text, new text) of an Edit, MultiEdit or Write."""
    tool_input = payload.get("tool_input", {})
    if "content" in tool_input:  # Write replaces the whole file
        return read_text(os.path.join(ROOT, rel)), str(tool_input["content"])
    edits = tool_input.get("edits") or [tool_input]
    return ("\n".join(str(e.get("old_string", "")) for e in edits),
            "\n".join(str(e.get("new_string", "")) for e in edits))


def ask(reason):
    """Prints a PreToolUse decision that asks the user."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason,
    }}))


def guard():
    """PreToolUse Edit|Write: asks the user before an edit to a kit file, or one that adds a dependency."""
    payload = read_payload()
    rel = edited_path(payload)
    if rel.startswith(GUARDED_PATHS):
        ask(f"{rel} is a guardrail file; a change can weaken the checks.")
        return
    dependencies = added_dependencies(rel, *edit_texts(payload, rel)) if rel else []
    if dependencies:
        ask(f"This edit adds a dependency to {rel}: {'; '.join(dependencies[:3])}")


def record():
    """PostToolUse Edit|Write: appends the edited code file to this session's file list."""
    payload = read_payload()
    rel = edited_path(payload)
    if rel.endswith(CODE_SUFFIXES) and not rel.startswith(".."):
        with open(session_file(payload), "a", encoding="utf-8") as handle:
            handle.write(rel + "\n")


def stop_hook():
    """Stop: runs the stop-stage checks on recorded files and files changed since the marker.

    On a pass, clears the state and moves the marker. On a failure, keeps the file list and exits 2
    so the agent gets the report; after MAX_FIX_ROUNDS failures in one turn it shows the report to
    the user instead and lets the turn stop.
    """
    payload = read_payload()
    files_path, rounds_path, marker = (session_file(payload, kind) for kind in ("files", "rounds", "marker"))
    files = sorted((set(read_text(files_path).split("\n")) | set(changed_since(marker))) - {""})
    if not files:
        return
    failures = run_checks("stop", files)
    if not failures:
        remove(files_path)
        remove(rounds_path)
        write_text(marker, "")
        return

    write_text(files_path, "\n".join(files) + "\n")
    report = "\n\n".join(failures)
    rounds = int(read_text(rounds_path) or 0) + 1
    if rounds > MAX_FIX_ROUNDS:
        remove(rounds_path)
        print(json.dumps({"systemMessage": f"Checks still fail after {MAX_FIX_ROUNDS} fix rounds:\n\n{report}"}))
        return
    write_text(rounds_path, str(rounds))
    print(f"Checks failed (round {rounds} of {MAX_FIX_ROUNDS}). Fix these before finishing:\n\n{report}", file=sys.stderr)
    sys.exit(2)

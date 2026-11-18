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
    "config/recomposition_screens.json",
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


def guard():
    """PreToolUse Edit|Write: asks the user before an edit to a file in GUARDED_PATHS."""
    rel = edited_path(read_payload())
    if rel.startswith(GUARDED_PATHS):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"{rel} is a guardrail file; a change can weaken the checks.",
        }}))


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

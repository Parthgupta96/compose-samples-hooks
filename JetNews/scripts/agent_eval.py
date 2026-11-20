#!/usr/bin/env python3
"""Deterministic checks for agent-written code. The checks live in scripts/agent_eval/.

Hooks (.claude/settings.json):
  --mark-turn   UserPromptSubmit: mark the start of the turn and reset the fix rounds
  --guard       PreToolUse Edit|Write: ask the user before an edit to a guardrail file
  --record      PostToolUse Edit|Write: remember the edited file for this session
  --stage stop  Stop: check the files this session edited, plus git-changed files written since the
                turn started; exit 2 sends failures back to the agent, at most 3 rounds per turn

By hand, against the git working tree:
  python3 scripts/agent_eval.py --install-tools               # ktlint, compose rules, detekt
  python3 scripts/agent_eval.py                               # ktlint, detekt, compile, stability
  python3 scripts/agent_eval.py --module app                  # same, limited to one module
  python3 scripts/agent_eval.py --stage device                # install, open screens, count recompositions
  python3 scripts/agent_eval.py --stage device --skip-install # use the build already on the device
  python3 scripts/agent_eval.py --self-check

Per-repo settings live in config/agent_eval.json; see SETUP.md.
"""
import argparse
import sys

from agent_eval import hooks
from agent_eval.checks import run_checks
from agent_eval.common import working_tree_files
from agent_eval.self_check import self_check
from agent_eval.tools import DETEKT, KTLINT, install_tools, tool


def run_manual(stage, module, device, skip_install):
    """Runs a stage against the git working tree and exits 1 on any failure.

    Args:
        stage: "manual", "device" or "release".
        module: Gradle module to limit the files to, for example "feature:impl"; empty for all.
        device: adb serial; empty for the only connected device.
        skip_install: device stage only; use the build already on the device.
    """
    files = working_tree_files()
    if module:
        prefix = module.replace(":", "/") + "/"
        files = [f for f in files if f.startswith(prefix)] or [prefix]
    if stage == "manual" and not (tool(KTLINT) and tool(DETEKT)):
        print("Note: ktlint or detekt is missing; run --install-tools.")
    failures = run_checks(stage, files, device, skip_install)
    if failures:
        print("\n\n".join(failures))
        sys.exit(1)
    print(f"Passed: {stage} checks on {len(files)} file(s).")


def main():
    """Parses the arguments and dispatches to a hook handler or a manual stage."""
    parser = argparse.ArgumentParser(description="Deterministic checks for agent-written code")
    parser.add_argument("--install-tools", action="store_true", help="Download pinned ktlint, compose rules, detekt")
    parser.add_argument("--mark-turn", action="store_true", help="UserPromptSubmit hook: mark the turn start")
    parser.add_argument("--guard", action="store_true", help="PreToolUse hook: ask before a guardrail file edit")
    parser.add_argument("--record", action="store_true", help="PostToolUse hook: remember the edited file")
    parser.add_argument("--stage", choices=["manual", "stop", "device", "release"], default="manual",
                        help="release: R8 build smoke test on the device; ask the user before running it")
    parser.add_argument("--module", default="", help="Check this Gradle module, e.g. app or feature:impl")
    parser.add_argument("--device", default="", help="adb serial")
    parser.add_argument("--skip-install", action="store_true", help="Device stage: use the installed build")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
    elif args.install_tools:
        install_tools()
    elif args.mark_turn:
        hooks.mark_turn()
    elif args.guard:
        hooks.guard()
    elif args.record:
        hooks.record()
    elif args.stage == "stop":
        hooks.stop_hook()
    else:
        run_manual(args.stage, args.module, args.device, args.skip_install)


if __name__ == "__main__":
    main()

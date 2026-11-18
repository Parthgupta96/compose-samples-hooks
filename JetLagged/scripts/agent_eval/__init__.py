"""Deterministic guardrail checks for agent-written code. The entry point is scripts/agent_eval.py.

Modules:
    common      paths, git queries and file helpers
    tools       pinned linter downloads and the linter runner
    lint        ktlint (with Compose rules) and detekt
    build       module graph and Gradle compile
    stability   Compose compiler stability reports
    device      recomposition counts on a connected device
    checks      the check registry and run_checks
    hooks       Claude Code hook handlers and per-session state
    self_check  assertions for the parsers
"""

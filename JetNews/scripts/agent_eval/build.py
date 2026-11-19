"""Gradle compile of the modules that own edited files."""
import subprocess

from .common import MAX_REPORTED_LINES, ROOT, gradle_modules, load_settings, module_of

COMPILE_TIMEOUT_SECONDS = 840  # stays under the Stop hook's 900s timeout in settings.json


def check_compile(ctx):
    """Compiles the Kotlin of each module that owns an edited file.

    The task name comes from compile_task in config/agent_eval.json; modules in
    skip_compile_modules are not compiled. The compile passes -PenableComposeReports, so
    check_compose_stability can read fresh reports.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Compiler error lines (at most MAX_REPORTED_LINES), a timeout line, or an empty list.
    """
    settings = load_settings()
    modules = gradle_modules()
    touched = {module_of(f, modules) for f in ctx.files} - {None} - set(settings["skip_compile_modules"])
    if not touched:
        return []
    tasks = [f":{module}:{settings['compile_task']}" for module in sorted(touched)]
    try:
        result = subprocess.run(
            ["./gradlew", *tasks, "--daemon", "-q", "--continue", "-PenableComposeReports"],
            cwd=ROOT, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return [f"Timed out after {COMPILE_TIMEOUT_SECONDS}s: {' '.join(tasks)}"]
    if result.returncode == 0:
        return []
    lines = (result.stderr + result.stdout).splitlines()
    errors = [line for line in lines if line.startswith("e: ") or ": error:" in line] or lines
    return errors[:MAX_REPORTED_LINES]

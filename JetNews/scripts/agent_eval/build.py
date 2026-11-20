"""Gradle compile of the modules that own edited files."""
import os
import subprocess

from .common import MAX_REPORTED_LINES, NO_SDK, ROOT, gradle_env, gradle_modules, load_settings, module_of, read_text
from .stability import module_report, report_is_stale

COMPILE_TIMEOUT_SECONDS = 840  # stays under the Stop hook's 900s timeout in settings.json


def gradle(tasks, env):
    """Runs Gradle tasks with Compose reports on.

    Args:
        tasks: task paths and options, for example [":app:compileDebugKotlin"].
        env: environment from gradle_env().

    Returns:
        Error lines (at most MAX_REPORTED_LINES), a timeout line, or an empty list.
    """
    try:
        result = subprocess.run(
            ["./gradlew", *tasks, "--daemon", "-q", "--continue", "-PenableComposeReports"],
            cwd=ROOT, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECONDS, env=env,
        )
    except subprocess.TimeoutExpired:
        return [f"Timed out after {COMPILE_TIMEOUT_SECONDS}s: {' '.join(tasks)}"]
    if result.returncode == 0:
        return []
    lines = (result.stderr + result.stdout).splitlines()
    errors = [line for line in lines if line.startswith("e: ") or ": error:" in line] or lines
    return errors[:MAX_REPORTED_LINES]


def check_compile(ctx):
    """Compiles the Kotlin of each module that owns an edited file, and keeps its Compose report fresh.

    The task name comes from compile_task in config/agent_eval.json; modules in
    skip_compile_modules are not compiled. When the agent already built a module without
    -PenableComposeReports, Gradle skips the compile as up to date and writes no report, so a module
    with edited composables and an old or missing report is compiled again with --rerun.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Compiler error lines, a timeout line, an "Inconclusive" line when there is no SDK, or an empty list.
    """
    settings = load_settings()
    modules = gradle_modules()
    owned = {}
    for rel in ctx.files:
        module = module_of(rel, modules)
        if module and module not in settings["skip_compile_modules"]:
            owned.setdefault(module, []).append(os.path.join(ROOT, rel))
    if not owned:
        return []
    env = gradle_env()
    if env is None:
        return [NO_SDK]
    task = settings["compile_task"]
    errors = gradle([f":{module}:{task}" for module in sorted(owned)], env)
    if errors:
        return errors
    stale = [module for module, sources in sorted(owned.items())
             if any(s.endswith(".kt") and "@Composable" in read_text(s) for s in sources)
             and report_is_stale((module_report(module) or [None])[0], sources)]
    # --rerun is a task option: it applies to the task just before it.
    return gradle([arg for module in stale for arg in (f":{module}:{task}", "--rerun")], env) if stale else []

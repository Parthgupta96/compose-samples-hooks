"""Android Lint, which runs the checks the project's libraries ship (Compose runtime, UI, foundation,
Material 3, Navigation, lifecycle and others) on top of the built-in ones.

Lint analyses a whole module, so findings are kept only on new files and changed lines. Version and
dependency-update warnings are dropped: the agent cannot act on them.
"""
import os
import subprocess
import time
import xml.etree.ElementTree as ET

from .build import COMPILE_TIMEOUT_SECONDS
from .common import NO_SDK, ROOT, gradle_env, gradle_modules, line_scope, load_settings, module_of

LINT_SUFFIXES = (".kt", ".java", ".xml", ".kts")
BLOCKING_SEVERITIES = {"Fatal", "Error", "Warning"}
# Dependency and SDK version advice: real, but not about the code the agent wrote.
VERSION_ADVICE = {"NewerVersionAvailable", "GradleDependency", "AndroidGradlePluginVersion", "OldTargetApi",
                  "SimilarGradleDependency", "GradleDynamicVersion"}


def parse_lint_xml(text):
    """Reads issues from a lint XML report.

    Args:
        text: contents of lint-results-<variant>.xml.

    Returns:
        (absolute file, line, severity, issue id, message) per issue with a location; line is 0 when
        the issue has no line.
    """
    issues = []
    for issue in ET.fromstring(text).iter("issue"):
        location = issue.find("location")
        if location is None or not location.get("file"):
            continue
        issues.append((location.get("file"), int(location.get("line") or 0), issue.get("severity"),
                       issue.get("id"), issue.get("message")))
    return issues


def report_path(module, lint_task):
    """The XML report a lint task writes, for example app/build/reports/lint-results-debug.xml."""
    variant = lint_task.removeprefix("lint")
    variant = variant[:1].lower() + variant[1:]
    return os.path.join(ROOT, module.replace(":", "/"), "build", "reports", f"lint-results-{variant}.xml")


def lint_findings(issues, scope, ignore):
    """Keeps the issues the agent must fix.

    Args:
        issues: parse_lint_xml result.
        scope: line_scope result; None means every line of a new file.
        ignore: issue ids to drop.

    Returns:
        "path:line message [id]" lines for blocking severities on new files and changed lines.
    """
    found = []
    for path, line, severity, issue_id, message in issues:
        rel = os.path.relpath(path, ROOT) if os.path.isabs(path) else path
        lines = scope.get(rel, set())
        if severity in BLOCKING_SEVERITIES and issue_id not in ignore and (lines is None or line in lines):
            found.append(f"{rel}:{line} {message} [{issue_id}]")
    return list(dict.fromkeys(found))


def check_android_lint(ctx):
    """Runs lint_task (default lintDebug) on each module that owns an edited file.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Lint findings on new files and changed lines, "Inconclusive" lines when lint wrote no report
        or there is no SDK, or an empty list.
    """
    settings = load_settings()
    scope = {rel: lines for rel, lines in line_scope(ctx.files, LINT_SUFFIXES).items() if lines != set()}
    modules = gradle_modules()
    owners = sorted({module_of(rel, modules) for rel in scope} - {None} - set(settings["skip_compile_modules"]))
    if not owners:
        return []
    env = gradle_env()
    if env is None:
        return [NO_SDK]
    task, started = settings["lint_task"], time.time()
    try:
        # Lint exits non-zero when it finds errors; the report says what they are.
        result = subprocess.run(["./gradlew", *[f":{m}:{task}" for m in owners], "--daemon", "-q", "--continue"],
                                cwd=ROOT, env=env, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return [f"Inconclusive: {task} timed out after {COMPILE_TIMEOUT_SECONDS}s."]
    ignore = VERSION_ADVICE | set(settings["lint_ignore"])
    findings, inconclusive = [], []
    for module in owners:
        report = report_path(module, task)
        # A report older than this run is valid when Gradle skipped lint as up to date (success), and
        # stale when the build failed before lint ran (for example a compile error).
        if not os.path.exists(report) or (result.returncode != 0 and os.path.getmtime(report) < started):
            inconclusive.append(f"Inconclusive: :{module}:{task} did not run (see the compile check); lint was not checked.")
            continue
        with open(report, encoding="utf-8") as handle:
            findings += lint_findings(parse_lint_xml(handle.read()), scope, ignore)
    return findings + inconclusive

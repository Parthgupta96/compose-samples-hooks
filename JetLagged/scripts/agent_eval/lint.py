"""ktlint with the Compose rules, and detekt.

Kotlin files new since HEAD are formatted with ktlint and checked on every line. Files that exist in
HEAD are not formatted; only their changed lines are checked, against Compose rules and detekt.
"""
import json
import os
import urllib.parse

from .common import ROOT, kotlin_scope
from .tools import COMPOSE_RULES, DETEKT, KTLINT, run_tool, tool, tool_failure

KTLINT_CONFIG = os.path.join(ROOT, "config", "ktlint.editorconfig")
DETEKT_CONFIG = os.path.join(ROOT, "config", "detekt.yml")


def check_ktlint(ctx):
    """Formats new Kotlin files and reports ktlint findings.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Failure lines as "path:line message [rule]". New files report every rule; old files report
        Compose rules on changed lines only. Empty when ktlint is not installed.
    """
    ktlint, compose = tool(KTLINT), tool(COMPOSE_RULES)
    if not (ktlint and compose):
        return []
    scope = kotlin_scope(ctx.files)
    new = [rel for rel, lines in scope.items() if lines is None]
    old = [rel for rel, lines in scope.items() if lines]
    findings = []
    for paths, fix in ((new, True), (old, False)):
        if not paths:
            continue
        command = ["java", "-jar", ktlint, f"--editorconfig={KTLINT_CONFIG}", "-R", compose,
                   "--relative", "--reporter=json,output={report}"] + (["-F"] if fix else []) + paths
        report, output = run_tool(command, ".json")
        if report is None:
            return tool_failure("ktlint", output)
        for entry in json.loads(report):
            rel = entry["file"]
            for error in entry["errors"]:
                if fix or (error["rule"].startswith("compose:") and error["line"] in scope.get(rel, ())):
                    message = error["message"].splitlines()[0]
                    findings.append(f"{rel}:{error['line']} {message} [{error['rule']}]")
    findings = list(dict.fromkeys(findings))  # ktlint reports a finding once per format pass
    if findings and new:
        findings.insert(0, "New files were formatted with ktlint; read them again before an edit.")
    return findings


def sarif_path(uri):
    """Converts a SARIF artifact URI to a repo-relative path.

    Args:
        uri: a file:// URI or a relative path, possibly percent-encoded.

    Returns:
        The repo-relative path.
    """
    path = urllib.parse.unquote(uri[len("file://"):] if uri.startswith("file://") else uri)
    return os.path.relpath(path, ROOT) if os.path.isabs(path) else path


def check_detekt(ctx):
    """Reports detekt findings on edited .kt files.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Failure lines as "path:line message [rule]", on every line of a new file and on changed
        lines of an old file. Empty when detekt is not installed.
    """
    detekt = tool(DETEKT)
    scope = {rel: lines for rel, lines in kotlin_scope(ctx.files).items() if rel.endswith(".kt") and lines != set()}
    if not detekt or not scope:
        return []
    command = ["java", "-jar", detekt, "--input", ",".join(scope), "--config", DETEKT_CONFIG,
               "--build-upon-default-config", "--report", "sarif:{report}"]
    report, output = run_tool(command, ".sarif")
    if report is None:
        return tool_failure("detekt", output)
    findings = []
    for result in json.loads(report)["runs"][0]["results"]:
        location = result["locations"][0]["physicalLocation"]
        rel, line = sarif_path(location["artifactLocation"]["uri"]), location["region"]["startLine"]
        lines = scope.get(rel, set())
        if lines is None or line in lines:
            findings.append(f"{rel}:{line} {result['message']['text']} [{result['ruleId']}]")
    return findings

"""ktlint with the Compose rules, and detekt.

Kotlin files new since HEAD are checked on every line, then formatted with ktlint; what the format
fixed is reported as "Autocorrected" lines, which never block a Stop. Files that exist in HEAD are not
formatted; only their changed lines are checked, against Compose rules and detekt. A project
.editorconfig overrides config/ktlint.editorconfig, so the hook follows the project's own style.
"""
import collections
import json
import os
import urllib.parse

from .common import ROOT, kotlin_scope
from .tools import COMPOSE_RULES, DETEKT, KTLINT, run_tool, tool, tool_failure

KTLINT_CONFIG = os.path.join(ROOT, "config", "ktlint.editorconfig")
DETEKT_CONFIG = os.path.join(ROOT, "config", "detekt.yml")
AUTOCORRECTED = "Autocorrected: "


def ktlint_errors(ktlint, compose, paths, fix):
    """Runs ktlint with the Compose rules.

    Args:
        ktlint, compose: tool paths.
        paths: repo-relative files.
        fix: True to format the files (-F); ktlint then reports only what it could not fix.

    Returns:
        ([(path, line, message, rule)], None), or (None, failure lines) when ktlint did not run.
    """
    command = ["java", "-jar", ktlint, f"--editorconfig={KTLINT_CONFIG}", "-R", compose,
               "--relative", "--reporter=json,output={report}"] + (["-F"] if fix else []) + paths
    report, output = run_tool(command, ".json")
    if report is None:
        return None, tool_failure("ktlint", output)
    return [(entry["file"], error["line"], error["message"].splitlines()[0], error["rule"])
            for entry in json.loads(report) for error in entry["errors"]], None


def autocorrected(before, after):
    """Finds the findings a format pass removed.

    Formatting shifts line numbers, so findings are matched on (path, message, rule) counts.

    Args:
        before: ktlint_errors from the check-only run.
        after: ktlint_errors from the -F run.

    Returns:
        The removed findings, with their line numbers from before the format.
    """
    left = collections.Counter((path, message, rule) for path, _, message, rule in after)
    fixed = []
    for finding in before:
        key = (finding[0], finding[2], finding[3])
        if left[key]:
            left[key] -= 1
        else:
            fixed.append(finding)
    return fixed


def check_ktlint(ctx):
    """Checks and formats new Kotlin files, and checks changed lines of old ones.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        Lines as "path:line message [rule]": what ktlint could not fix, then "Autocorrected" lines for
        what it fixed in new files. Old files report Compose rules on changed lines only. Empty when
        ktlint is not installed.
    """
    ktlint, compose = tool(KTLINT), tool(COMPOSE_RULES)
    if not (ktlint and compose):
        return []
    scope = kotlin_scope(ctx.files)
    new = [rel for rel, lines in scope.items() if lines is None]
    old = [rel for rel, lines in scope.items() if lines]
    findings, fixed = [], []
    if new:
        before, failure = ktlint_errors(ktlint, compose, new, fix=False)
        after, failure = (before, failure) if failure else ktlint_errors(ktlint, compose, new, fix=True)
        if failure:
            return failure
        findings += after
        fixed = autocorrected(before, after)
    if old:
        errors, failure = ktlint_errors(ktlint, compose, old, fix=False)
        if failure:
            return failure
        findings += [e for e in errors if e[3].startswith("compose:") and e[1] in scope[e[0]]]
    lines = list(dict.fromkeys(f"{path}:{line} {message} [{rule}]" for path, line, message, rule in findings))
    if lines and fixed:
        lines.insert(0, "New files were formatted with ktlint; read them again before an edit.")
    return lines + [f"{AUTOCORRECTED}{path}:{line} {message} [{rule}]" for path, line, message, rule in fixed]


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

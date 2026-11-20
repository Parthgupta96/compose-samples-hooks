"""Compose compiler stability reports: unstable parameters of edited composables and unstable UI models.

The reports live in <module>/build/compose_compiler and are written by a compile with
-PenableComposeReports (see the reports block in SETUP.md). The newest report is used, so file names
with or without a variant both work; report_variant in config/agent_eval.json can force one.
"""
import glob
import os
import re

from .common import ROOT, gradle_modules, kotlin_scope, load_settings, module_of, read_text

COMPOSABLE_DECL = re.compile(
    r"@Composable\s+(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:private|internal|public|inline)\s+)*"
    r"fun\s+(?:[\w.<>]+\.)?(\w+)\s*\("
)
CLASS_DECL = re.compile(r"\bclass\s+(\w+)")
STABILITY_FIX = (
    "Fix: ImmutableList / ImmutableSet / ImmutableMap (kotlinx.collections.immutable) for collections, "
    "val for fields, or @Immutable when the type is deeply immutable."
)


def declarations(text, pattern):
    """Finds declarations and the lines their parameter lists span.

    Args:
        text: Kotlin source.
        pattern: COMPOSABLE_DECL or CLASS_DECL; group 1 is the name.

    Returns:
        (name, first line, last line) per match. A declaration with no "(" on its line spans one line.
    """
    found = []
    for match in pattern.finditer(text):
        start = match.start(1)
        line_end = text.find("\n", start) % (len(text) + 1)
        end = text.find("(", start)
        if end == -1 or end > line_end:
            end = line_end
        else:
            depth = 0
            for end in range(end, len(text)):
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                if depth == 0:
                    break
        found.append((match.group(1), text.count("\n", 0, start) + 1, text.count("\n", 0, end) + 1))
    return found


def parse_stability_reports(composables, classes):
    """Reads the unstable parameters and classes from Compose compiler reports.

    Args:
        composables: text of the *-composables.txt reports.
        classes: text of the *-classes.txt reports.

    Returns:
        ({composable name: unstable parameter names}, {unstable class names}). Composables with the
        same name share one entry. kotlinx.serialization "$serializer" classes are not returned.
    """
    params, current = {}, None
    for line in composables.splitlines():
        header = re.search(r"\bfun (?:[\w.]+\.)?(\w+)\($", line)  # Kotlin 2.4+ prefixes the package
        if header:
            current = params.setdefault(header.group(1), [])
        elif line.startswith(")"):
            current = None
        elif current is not None:
            # Only the "unstable" label counts. An unlabeled parameter has runtime stability, which the
            # Compose docs do not treat as a problem under strong skipping (compared with ===).
            param = re.match(r"\s+unstable (\w+):", line)
            if param:
                current.append(param.group(1))
    unstable = {
        name.rsplit(".", 1)[-1]
        for name in re.findall(r"^unstable class ([\w$.]+) \{", classes, re.M)
        if "$" not in name
    }
    return params, unstable


def report_files(report_dir, variant=""):
    """Picks the composables report and its classes report in one folder.

    Kotlin 2.4+ writes app-composables.txt and older versions app-debug-composables.txt, so the newest
    *-composables.txt is used: the compile that just ran wrote it.

    Args:
        report_dir: the module's build/compose_compiler folder.
        variant: optional; only files ending in <variant>-composables.txt count.

    Returns:
        (composables path, classes path), or None when there is no report.
    """
    found = glob.glob(os.path.join(report_dir, f"*{variant}-composables.txt"))
    if not found:
        return None
    composables = max(found, key=os.path.getmtime)
    return composables, composables[: -len("composables.txt")] + "classes.txt"


def stability_reports(module):
    """Loads the stability reports of one module.

    Args:
        module: module path, for example "feature:impl".

    Returns:
        The parse_stability_reports result, or None when the module has no report.
    """
    files = module_report(module)
    return parse_stability_reports(*(read_text(f) for f in files)) if files else None


def module_report(module):
    """Finds a module's newest Compose report.

    Args:
        module: Gradle module path, for example "app".

    Returns:
        (composables report, classes report) paths, or None when the module has no report.
    """
    report_dir = os.path.join(ROOT, module.replace(":", "/"), "build", "compose_compiler")
    return report_files(report_dir, load_settings()["report_variant"])


def report_is_stale(report, sources):
    """Tells whether a Compose report predates the sources it should describe.

    A compile that Gradle skips as up to date writes no report, so an agent's own build without
    -PenableComposeReports leaves the previous report in place.

    Args:
        report: path of the composables report, or None.
        sources: absolute paths of edited Kotlin files.

    Returns:
        True when the report is missing or older than the newest existing source.
    """
    if not report or not os.path.exists(report):
        return True
    newest = max((os.path.getmtime(s) for s in sources if os.path.exists(s)), default=0)
    return os.path.getmtime(report) < newest


def check_compose_stability(ctx):
    """Reports unstable parameters and unstable UI model classes in edited code.

    A composable is checked when its file is new or a changed line falls in its signature. A class is
    checked only in a *UIModel.kt file, under the same rule.

    Args:
        ctx: check context; uses ctx.files. Run after check_compile.

    Returns:
        Failure lines plus one fix hint, or an empty list.
    """
    # ponytail: an incremental compile reports only the files it recompiled, so a declaration that is
    # absent from the reports is skipped, not failed. Run a clean compile with reports to cover it.
    modules, reports, findings, inconclusive = gradle_modules(), {}, [], []
    for rel, lines in kotlin_scope(ctx.files).items():
        module = module_of(rel, modules)
        if not rel.endswith(".kt") or lines == set() or not module:
            continue
        if module not in reports:
            reports[module] = stability_reports(module)
            if reports[module] is None:
                inconclusive.append(f"Inconclusive: no Compose report for {module}; nothing was checked. "
                                    "Compile with -PenableComposeReports (see SETUP.md).")
                reports[module] = ({}, set())
            else:
                sources = [os.path.join(ROOT, f) for f in ctx.files if module_of(f, modules) == module]
                if report_is_stale(module_report(module)[0], sources):
                    inconclusive.append(f"Inconclusive: the Compose report for {module} is older than the edited "
                                        "files, so it may not cover them.")
        params, unstable_classes = reports[module]
        text = read_text(os.path.join(ROOT, rel))
        touched = lambda first, last: lines is None or any(first <= n <= last for n in lines)
        for name, first, last in declarations(text, COMPOSABLE_DECL):
            if touched(first, last) and params.get(name):
                findings.append(f"{rel}:{first} {name} has unstable parameters: {', '.join(params[name])}")
        if rel.endswith("UIModel.kt"):
            for name, first, last in declarations(text, CLASS_DECL):
                if touched(first, last) and name in unstable_classes:
                    findings.append(f"{rel}:{first} class {name} is unstable")
    return (findings + [STABILITY_FIX] if findings else []) + inconclusive

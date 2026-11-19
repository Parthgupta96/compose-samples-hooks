"""Paths, per-repo settings, git queries and small file helpers shared by every check."""
import json
import os
import re
import subprocess

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SETTINGS_FILE = os.path.join(ROOT, "config", "agent_eval.json")
CODE_SUFFIXES = (".kt", ".java", ".xml", ".gradle", ".kts")
KOTLIN_SUFFIXES = (".kt", ".kts")
MAX_REPORTED_LINES = 40
DEFAULT_SETTINGS = {
    "compile_task": "compileDebugKotlin",
    "report_variant": "",
    "skip_compile_modules": [],
    "device_in_stop": False,
}


def load_settings():
    """Reads config/agent_eval.json over DEFAULT_SETTINGS.

    Returns:
        The merged settings dict. A missing or invalid file gives the defaults.
    """
    try:
        overrides = json.loads(read_text(SETTINGS_FILE) or "{}")
    except ValueError:
        overrides = {}
    return {**DEFAULT_SETTINGS, **overrides}


def parse_includes(settings_text):
    """Reads the module paths from the include lines of a Gradle settings file.

    Args:
        settings_text: contents of settings.gradle or settings.gradle.kts.

    Returns:
        Module paths without the leading colon, for example "feature:impl". Commented-out
        include lines are not returned.
    """
    includes = [line for line in settings_text.splitlines() if line.lstrip().startswith("include")]
    return re.findall(r"""["']:([\w:-]+)["']""", "\n".join(includes))


def gradle_modules():
    """Lists the Gradle modules that the root settings file includes.

    Returns:
        Module paths from settings.gradle or settings.gradle.kts; empty when neither exists.
    """
    for name in ("settings.gradle.kts", "settings.gradle"):
        text = read_text(os.path.join(ROOT, name))
        if text:
            return parse_includes(text)
    return []


def module_of(path, modules):
    """Finds the innermost Gradle module that owns a file.

    Args:
        path: repo-relative file path.
        modules: module paths from gradle_modules().

    Returns:
        The owning module path, or None when no module owns the file.
    """
    owners = [m for m in modules if path.startswith(m.replace(":", "/") + "/")]
    return max(owners, key=len, default=None)


def working_tree_files():
    """Lists code files that differ from HEAD, tracked or untracked.

    Returns:
        Repo-relative paths that end with one of CODE_SUFFIXES. Ignored files are not returned.
    """
    tracked = ["git", "diff", "--name-only", "--relative", "-z", "HEAD"]
    untracked = ["git", "ls-files", "-o", "--exclude-standard", "-z"]
    files = []
    for command in (tracked, untracked):
        output = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout
        files += [f for f in output.split("\0") if f.endswith(CODE_SUFFIXES)]
    return files


def parse_hunks(diff):
    """Reads the added or changed line numbers from a diff.

    Args:
        diff: output of `git diff -U0`.

    Returns:
        A set of new-side line numbers. A hunk that only deletes lines adds nothing.
    """
    lines = set()
    for start, count in re.findall(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
        lines.update(range(int(start), int(start) + (int(count) if count else 1)))
    return lines


def kotlin_scope(files):
    """Finds which lines of each Kotlin file a check must report on.

    Args:
        files: repo-relative paths; non-Kotlin and deleted files are skipped.

    Returns:
        A dict from path to None for a file that is new since HEAD (every line), or to the set of
        lines changed since HEAD. An empty set means the file only lost lines.
    """
    scope = {}
    for rel in files:
        if not rel.endswith(KOTLIN_SUFFIXES) or not os.path.exists(os.path.join(ROOT, rel)):
            continue
        in_head = subprocess.run(["git", "cat-file", "-e", f"HEAD:./{rel}"], cwd=ROOT, capture_output=True)
        if in_head.returncode != 0:
            scope[rel] = None
        else:
            diff = subprocess.run(["git", "diff", "-U0", "HEAD", "--", rel], cwd=ROOT, capture_output=True, text=True)
            scope[rel] = parse_hunks(diff.stdout)
    return scope


def read_text(path):
    """Reads a UTF-8 file.

    Args:
        path: absolute path.

    Returns:
        The file text, or an empty string when the file cannot be read.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def write_text(path, text):
    """Writes a UTF-8 file, replacing its contents.

    Args:
        path: absolute path.
        text: new contents.
    """
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def remove(path):
    """Deletes a file. A missing file is not an error.

    Args:
        path: absolute path.
    """
    try:
        os.remove(path)
    except OSError:
        pass

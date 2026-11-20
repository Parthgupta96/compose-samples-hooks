"""Paths, per-repo settings, git queries and small file helpers shared by every check."""
import json
import os
import re
import shutil
import subprocess

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SETTINGS_FILE = os.path.join(ROOT, "config", "agent_eval.json")
CODE_SUFFIXES = (".kt", ".java", ".xml", ".gradle", ".kts")
KOTLIN_SUFFIXES = (".kt", ".kts")
MAX_REPORTED_LINES = 40
DEFAULT_SETTINGS = {
    "compile_task": "compileDebugKotlin",
    "lint_task": "lintDebug",
    "lint_ignore": [],
    "report_variant": "",
    "skip_compile_modules": [],
    "device_in_stop": False,
}


SDK_GUESSES = ("~/Library/Android/sdk", "~/Android/Sdk", os.path.join("%LOCALAPPDATA%", "Android", "Sdk"))
NO_SDK = ("Inconclusive: no Android SDK found, so Gradle cannot run; nothing was compiled. Set ANDROID_HOME, "
          "or sdk.dir in local.properties.")


def find_sdk(local_properties, environ, adb_path, is_dir=os.path.isdir):
    """Finds the Android SDK the way Gradle would, plus two fallbacks Gradle does not try.

    Hooks run in the Claude Code process, which may lack the shell profile's ANDROID_HOME.

    Args:
        local_properties: text of local.properties, or "".
        environ: environment variables.
        adb_path: resolved path of adb on PATH, or None; its grandparent is the SDK.
        is_dir: directory test, replaceable in the self-check.

    Returns:
        (sdk path, whether Gradle finds it without help), or (None, False) when there is no SDK.
    """
    match = re.search(r"^\s*sdk\.dir\s*=\s*(.+?)\s*$", local_properties, re.M)
    if match:
        return match.group(1).replace("\\:", ":").replace("\\\\", "\\"), True
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if environ.get(var):
            return environ[var], True
    candidates = [os.path.dirname(os.path.dirname(adb_path))] if adb_path else []
    candidates += [os.path.expandvars(os.path.expanduser(guess)) for guess in SDK_GUESSES]
    return next(((path, False) for path in candidates if is_dir(os.path.join(path, "platforms"))), (None, False))


def gradle_env():
    """The environment for a Gradle run, with ANDROID_HOME added when Gradle would not find the SDK.

    Returns:
        An environment dict, or None when no SDK exists (callers report NO_SDK).
    """
    adb = shutil.which("adb")
    sdk, found_by_gradle = find_sdk(read_text(os.path.join(ROOT, "local.properties")), os.environ,
                                    os.path.realpath(adb) if adb else None)
    if sdk is None:
        return None
    return dict(os.environ) if found_by_gradle else {**os.environ, "ANDROID_HOME": sdk}


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
    """line_scope for Kotlin files (.kt, .kts)."""
    return line_scope(files, KOTLIN_SUFFIXES)


def line_scope(files, suffixes):
    """Finds which lines of each file a check must report on.

    Args:
        files: repo-relative paths; files without one of the suffixes and deleted files are skipped.
        suffixes: file name endings to keep.

    Returns:
        A dict from path to None for a file that is new since HEAD (every line), or to the set of
        lines changed since HEAD. An empty set means the file only lost lines.
    """
    scope = {}
    for rel in files:
        if not rel.endswith(suffixes) or not os.path.exists(os.path.join(ROOT, rel)):
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

"""App health during device measurements: crashes, ANRs and StrictMode violations, read from logcat.

StrictMode needs the debug-only StrictModeInstaller provider (see SETUP.md, section 6), which turns on
every policy with log penalties. A violation counts only when a frame of its stack is in a file the
agent edited, so violations in the framework, libraries or untouched app code (for example disk reads
during startup) never block.
"""
import re
import subprocess

LOG_TAGS = ["StrictMode:D", "AndroidRuntime:E", "ActivityManager:E", "*:S"]
FRAME = re.compile(r"at ([\w$.]+)\.[\w$<>-]+\(([\w$]+\.(?:kt|java)):(\d+)\)")
VIOLATION = re.compile(r"android\.os\.strictmode\.(\w+)")


def health_logs(adb):
    """Dumps the StrictMode, crash and ANR lines from the main, system and crash buffers.

    Args:
        adb: adb command prefix.

    Returns:
        The logcat text.
    """
    command = adb + ["logcat", "-d", "-b", "main", "-b", "system", "-b", "crash", "-s", *LOG_TAGS]
    return subprocess.run(command, capture_output=True, text=True).stdout


def clear_logs(adb):
    """Clears the buffers health_logs reads."""
    subprocess.run(adb + ["logcat", "-c", "-b", "main", "-b", "system", "-b", "crash"], capture_output=True)


def payloads(log, tag):
    """The message part of each logcat line with the given tag, in order."""
    marker = f" {tag}: "
    return [line.split(marker, 1)[1] for line in log.splitlines() if marker in line]


def edited_frame(line, sources):
    """Maps a stack frame line to "path:line" when it is in one of the edited files, else None."""
    frame = FRAME.search(line)
    if not frame:
        return None
    suffix = "/" + frame.group(1).rsplit(".", 1)[0].replace(".", "/") + "/" + frame.group(2)
    rel = next((f for f in sources if f.endswith(suffix)), None)
    return f"{rel}:{frame.group(3)}" if rel else None


def parse_crashes(log, package, files=()):
    """Finds crashes of the app.

    Args:
        log: health_logs text.
        package: application id.
        files: repo-relative paths the agent edited; a frame in one of them is reported as path:line.

    Returns:
        One line per crash: the root cause (the last "Caused by"), and where it happened: a frame in an
        edited file, else the first frame in the app's package, else the first frame.
    """
    sources = [f for f in files if f.endswith((".kt", ".java"))]
    lines = [line.strip() for line in payloads(log, "AndroidRuntime")]
    crashes = []
    for i, line in enumerate(lines):
        if not (line.startswith("FATAL EXCEPTION") and i + 1 < len(lines) and lines[i + 1].startswith(f"Process: {package},")):
            continue
        block = lines[i + 2:]
        block = block[:next((n for n, b in enumerate(block) if b.startswith("FATAL EXCEPTION")), len(block))]
        causes = [b.removeprefix("Caused by: ") for b in block if b.startswith("Caused by: ")]
        cause = causes[-1] if causes else (block[0] if block else "unknown exception")
        frames = [b for b in block if b.startswith("at ")]
        where = next((w for w in (edited_frame(f, sources) for f in frames) if w), None)
        where = where or next((f for f in frames if f.startswith(f"at {package}.")), frames[0] if frames else "")
        crashes.append(f"The app crashed: {cause}" + (f" ({where})" if where else ""))
    return crashes


def parse_anrs(log, package):
    """Finds ANRs (app not responding) of the app.

    Returns:
        One line per ANR.
    """
    return [f"The app stopped responding: {line.strip()}" for line in payloads(log, "ActivityManager")
            if re.match(rf"ANR in {re.escape(package)}\b", line)]


def parse_strictmode(log, files):
    """Finds StrictMode violations raised from code in the edited files.

    Args:
        log: health_logs text.
        files: repo-relative paths the agent edited.

    Returns:
        "StrictMode <Violation> at path:line" lines, one per violation and place.
    """
    sources = [f for f in files if f.endswith((".kt", ".java"))]
    found, violation = [], None
    for line in payloads(log, "StrictMode"):
        if "policy violation" in line:
            kind = VIOLATION.search(line)
            violation = kind.group(1) if kind else "violation"
            continue
        where = edited_frame(line, sources) if violation else None
        if where:
            found.append(f"StrictMode {violation} at {where}. Move this work off the main thread.")
            violation = None  # one place per violation: the innermost edited frame
    return list(dict.fromkeys(found))


def app_problems(log, package, files):
    """Crashes, ANRs and StrictMode violations from edited code; all of them block a Stop."""
    return parse_crashes(log, package, files) + parse_anrs(log, package) + parse_strictmode(log, files)

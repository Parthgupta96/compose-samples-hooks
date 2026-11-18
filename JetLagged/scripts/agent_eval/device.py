"""Recomposition counts on a connected device, read from RecomposeTracker logcat lines.

A composable takes part when it uses Modifier.recomposeHighlighter("Tag") in a changed .kt file and
config/recomposition_screens.json maps the tag to a screen:

    {
      "package": "com.example.app",
      "build_task": ":app:assembleDebug",
      "screens": {
        "Tag": {"deeplink": "https://example.com/history", "gesture": "swipe_up"}
      }
    }

package and build_task must name the same build variant (an applicationIdSuffix changes the package).

gesture is "swipe_up" (default), "swipe_down" or "none". The project's recomposeHighlighter modifier
must log, under the logcat tag RecomposeTracker, "Composable <Tag> attached" when a tagged node first
appears and "Composable <Tag> count=<n>" on each recomposition; see SETUP.md. The count must reset
after a short idle time (the reference modifier uses 3s).
"""
import glob
import json
import os
import re
import shlex
import subprocess
import time

from .common import ROOT, read_text

SCREEN_MAP = os.path.join(ROOT, "config", "recomposition_screens.json")
TRACKER_TAG = "RecomposeTracker"
DEFAULT_BUILD_TASK = ":app:assembleDebug"
INSTALL_TIMEOUT_SECONDS = 1800
SETTLE_SECONDS = 8  # screen load plus the highlighter's 3s count reset
GESTURE_SECONDS = 1.5
GESTURES = {"swipe_up", "swipe_down", "none"}
MAX_RECOMPOSITIONS_ON_SCROLL = 2


def recomposition_tags(files):
    """Finds the recomposeHighlighter tags in edited Kotlin files.

    Args:
        files: repo-relative paths; only .kt files are read.

    Returns:
        The set of tag strings. A tag must be word characters only.
    """
    tags = set()
    for rel in files:
        if rel.endswith(".kt"):
            tags.update(re.findall(r'recomposeHighlighter\s*\(\s*(?:tag\s*=\s*)?"(\w+)"', read_text(os.path.join(ROOT, rel))))
    return tags


def parse_recomposition_counts(logcat):
    """Reads the highest count logged per tag.

    Args:
        logcat: RecomposeTracker logcat text.

    Returns:
        {tag: highest count}.
    """
    counts = {}
    for name, count in re.findall(r"Composable\s+(\w+)\s+count=(\d+)", logcat):
        counts[name] = max(counts.get(name, 0), int(count))
    return counts


def parse_attached(logcat):
    """Reads the tags whose nodes appeared on screen.

    Args:
        logcat: RecomposeTracker logcat text.

    Returns:
        The set of tags with an "attached" line.
    """
    return set(re.findall(r"Composable\s+(\w+)\s+attached", logcat))


def gesture_command(adb, gesture, width, height):
    """Builds the adb swipe for a gesture across the middle 40% of the screen.

    Args:
        adb: adb command prefix, with -s when a serial is set.
        gesture: one of GESTURES.
        width: screen width in pixels.
        height: screen height in pixels.

    Returns:
        The argument list, or None for "none".
    """
    if gesture == "none":
        return None
    x, top, bottom = width // 2, height * 3 // 10, height * 7 // 10
    start, end = (bottom, top) if gesture == "swipe_up" else (top, bottom)
    return adb + ["shell", "input", "swipe", str(x), str(start), str(x), str(end), "400"]


def screen_size(adb):
    """Reads the device screen size.

    Args:
        adb: adb command prefix.

    Returns:
        (width, height) in pixels; the override size when one is set. (1080, 2400) when unreadable.
    """
    sizes = re.findall(r"(\d+)x(\d+)", subprocess.run(adb + ["shell", "wm", "size"], capture_output=True, text=True).stdout)
    return tuple(map(int, sizes[-1])) if sizes else (1080, 2400)


def tracker_logs(adb):
    """Dumps the RecomposeTracker lines from the logcat buffer.

    Args:
        adb: adb command prefix.

    Returns:
        The logcat text.
    """
    return subprocess.run(adb + ["logcat", "-d", "-s", f"{TRACKER_TAG}:D"], capture_output=True, text=True).stdout


def gradle_failure(output):
    """Extracts the reason from a failed Gradle run.

    Args:
        output: combined Gradle stdout and stderr.

    Returns:
        The "What went wrong" section and compiler errors, or the last 10 lines when neither exists.
    """
    lines = [line for line in output.splitlines() if line.strip()]
    if "* What went wrong:" in lines:
        start = lines.index("* What went wrong:")
        return lines[start + 1:start + 6]
    return [line for line in lines if line.startswith("e: ")][:10] or lines[-10:]


def install_build(adb, build_task):
    """Builds the APK with Gradle and installs it over the app on the device.

    `adb install -r -d` keeps the app data and allows a lower versionCode; the downgrade works only
    when the installed app is debuggable.

    Args:
        adb: adb command prefix.
        build_task: Gradle assemble task, for example ":app:assembleDebug".

    Returns:
        Failure lines, or an empty list on success.
    """
    try:
        result = subprocess.run(["./gradlew", build_task, "--daemon", "-q"], cwd=ROOT,
                                capture_output=True, text=True, timeout=INSTALL_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return [f"Build timed out after {INSTALL_TIMEOUT_SECONDS}s: {build_task}"]
    if result.returncode != 0:
        return [f"Build failed: {build_task}"] + gradle_failure(result.stderr + result.stdout)

    module_dir = os.path.join(ROOT, *build_task.strip(":").split(":")[:-1])
    apks = glob.glob(os.path.join(module_dir, "build", "outputs", "apk", "**", "*.apk"), recursive=True)
    if not apks:
        return [f"Build produced no APK under {os.path.relpath(module_dir, ROOT)}/build/outputs/apk."]
    apk = max(apks, key=os.path.getmtime)
    install = subprocess.run(adb + ["install", "-r", "-d", apk], capture_output=True, text=True)
    if "Success" not in install.stdout:
        return [f"Install failed: {os.path.relpath(apk, ROOT)}", (install.stdout + install.stderr).strip()]
    return []


def measure_screen(adb, package, deeplink, gesture, size, tags):
    """Opens one screen, waits for the counts to reset, performs the gesture and compares the counts.

    Args:
        adb: adb command prefix.
        package: application id that handles the deep link.
        deeplink: URL that opens the screen.
        gesture: one of GESTURES.
        size: (width, height) from screen_size().
        tags: tags expected on this screen.

    Returns:
        Failure lines: a count above MAX_RECOMPOSITIONS_ON_SCROLL, or "Inconclusive" when a tag
        logged nothing or the screen did not open.
    """
    if gesture not in GESTURES:
        return [f"Inconclusive: unknown gesture {gesture!r} for {', '.join(tags)}."]
    subprocess.run(adb + ["logcat", "-c"], capture_output=True)
    start = subprocess.run(adb + ["shell", "am", "start", "-W", "-a", "android.intent.action.VIEW",
                                  "-d", shlex.quote(deeplink), package], capture_output=True, text=True)
    if "Error" in start.stdout + start.stderr:
        return [f"Inconclusive: could not open {deeplink} in {package}: {(start.stdout + start.stderr).strip()}"]
    time.sleep(SETTLE_SECONDS)
    loaded = tracker_logs(adb)

    subprocess.run(adb + ["logcat", "-c"], capture_output=True)
    swipe = gesture_command(adb, gesture, *size)
    if swipe:
        subprocess.run(swipe, capture_output=True)
    time.sleep(GESTURE_SECONDS)
    during = tracker_logs(adb)

    counts = parse_recomposition_counts(during)
    seen = parse_attached(loaded) | parse_attached(during) | parse_recomposition_counts(loaded).keys() | counts.keys()
    errors = []
    for tag in tags:
        if tag not in seen:
            errors.append(f"Inconclusive: no {TRACKER_TAG} log for {tag} on {deeplink}; check that the screen opened.")
        elif counts.get(tag, 0) > MAX_RECOMPOSITIONS_ON_SCROLL:
            errors.append(f"{tag} recomposed {counts[tag]} times during {gesture} (max {MAX_RECOMPOSITIONS_ON_SCROLL}).")
    return errors


def check_recomposition(ctx):
    """Installs the build, opens each mapped screen and checks the recomposition count of each tag.

    Args:
        ctx: check context; uses ctx.files, ctx.device and ctx.skip_install.

    Returns:
        Failure lines; "Inconclusive" lines when a tag, the screen map, adb or the device is missing.
    """
    tags = recomposition_tags(ctx.files)
    if not tags:
        return ['Inconclusive: no recomposeHighlighter("Tag") in the changed .kt files.']
    try:
        screen_map = json.loads(read_text(SCREEN_MAP))
    except ValueError:
        return [f"Inconclusive: {os.path.relpath(SCREEN_MAP, ROOT)} is missing or not valid JSON."]
    screens = screen_map.get("screens", {})
    errors = [f"Inconclusive: no entry for {tag} in config/recomposition_screens.json." for tag in sorted(tags - screens.keys())]
    mapped = sorted(tag for tag in tags & screens.keys() if screens[tag].get("deeplink"))
    errors += [f"Inconclusive: no deeplink for {tag}." for tag in sorted(tags & screens.keys()) if tag not in mapped]
    if not mapped:
        return errors

    adb = ["adb"] + (["-s", ctx.device] if ctx.device else [])
    try:
        devices = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    except OSError:
        return errors + ["Inconclusive: adb is not on PATH."]
    if f"{ctx.device}\tdevice" not in devices:
        return errors + ["Inconclusive: no authorised device connected."]
    if not ctx.skip_install:
        install_errors = install_build(adb, screen_map.get("build_task", DEFAULT_BUILD_TASK))
        if install_errors:
            return errors + install_errors

    size, by_screen = screen_size(adb), {}
    for tag in mapped:
        entry = screens[tag]
        by_screen.setdefault((entry["deeplink"], entry.get("gesture", "swipe_up")), []).append(tag)
    for (deeplink, gesture), screen_tags in by_screen.items():
        errors += measure_screen(adb, screen_map.get("package", ""), deeplink, gesture, size, screen_tags)
    return errors

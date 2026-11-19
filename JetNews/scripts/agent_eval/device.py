"""Device checks: recomposition counts from RecomposeTracker logcat lines, and frame times from gfxinfo.

A composable takes part when it uses Modifier.recomposeHighlighter("Tag") in a changed .kt file and
config/recomposition_screens.json maps the tag to a screen:

    {
      "package": "com.example.app",
      "build_task": ":app:assembleDebug",
      "gfx_build_task": ":app:assembleBenchmark",
      "max_janky_percent": 10,
      "max_p95_ms": 24,
      "screens": {
        "Row": {"deeplink": "https://example.com/history", "gesture": "swipe_up"},
        "Card": {"preview": "com.example.ui.CardKt.CardPreview"},
        "Item": {"steps": [{"tap_desc": "Open menu"}, {"tap_text": "History"}]}
      }
    }

A screen opens one of three ways: a deep link, a @Preview through ui-tooling's PreviewActivity (debug
builds only), or steps that launch the app and tap nodes found by text or content description.

package and build_task must name the same build variant (an applicationIdSuffix changes the package).
gfx_build_task is optional: when set, frames are measured on that variant (for example a
non-debuggable benchmark build), which cannot open a preview. max_janky_percent and max_p95_ms are
optional and may be overridden per screen; without them the frame check only reports.

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
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .common import ROOT, read_text

SCREEN_MAP = os.path.join(ROOT, "config", "recomposition_screens.json")
TRACKER_TAG = "RecomposeTracker"
DEFAULT_BUILD_TASK = ":app:assembleDebug"
PREVIEW_ACTIVITY = "androidx.compose.ui.tooling.PreviewActivity"
INSTALL_TIMEOUT_SECONDS = 1800
SETTLE_SECONDS = 8  # screen load plus the highlighter's 3s count reset
LAUNCH_SECONDS = 4
STEP_SECONDS = 1.5
GESTURE_SECONDS = 1.5
GESTURES = {"swipe_up", "swipe_down", "none"}
MAX_RECOMPOSITIONS_ON_SCROLL = 2
DEFAULT_GESTURE_REPEATS = 5
DEFAULT_FRAME_RUNS = 3
UI_DUMP = "/sdcard/agent_eval_ui.xml"


def info(line):
    """Prints a measurement on stderr, which a passing Stop hook does not send to the agent."""
    print(line, file=sys.stderr)


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


def parse_gfxinfo(text):
    """Reads the process-level frame stats from `dumpsys gfxinfo <package>`.

    Args:
        gfxinfo output.

    Returns:
        {"frames", "janky", "janky_percent", "p50", "p90", "p95", "p99"}; keys whose line is missing
        are left out. GPU percentiles and the legacy janky count are not read.
    """
    stats = {}
    frames = re.search(r"^\s*Total frames rendered: (\d+)", text, re.M)
    janky = re.search(r"^\s*Janky frames: (\d+) \(([\d.]+)%\)", text, re.M)
    if frames:
        stats["frames"] = int(frames.group(1))
    if janky:
        stats["janky"], stats["janky_percent"] = int(janky.group(1)), float(janky.group(2))
    for percentile, ms in re.findall(r"^\s*(\d+)th percentile: (\d+)ms", text, re.M):
        stats.setdefault(f"p{percentile}", int(ms))
    return stats


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


def launch_command(adb, package, entry):
    """Builds the `am start` command for a deep link or preview screen.

    Args:
        adb: adb command prefix.
        package: application id.
        entry: screen map entry.

    Returns:
        The argument list, or None for a steps screen.
    """
    if entry.get("preview"):
        return adb + ["shell", "am", "start", "-W", "-n", f"{package}/{PREVIEW_ACTIVITY}", "--es", "composable", entry["preview"]]
    if entry.get("deeplink"):
        return adb + ["shell", "am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", shlex.quote(entry["deeplink"]), package]
    return None


def screen_label(entry):
    """Names a screen entry in messages."""
    return entry.get("preview") or entry.get("deeplink") or "steps " + json.dumps(entry.get("steps", []))


def find_node(ui_xml, step):
    """Finds the centre of the first node a step names.

    Args:
        ui_xml: `uiautomator dump` output.
        step: {"tap_text": text} or {"tap_desc": content description}.

    Returns:
        (x, y), or None when no node matches.
    """
    attribute, value = ("content-desc", step["tap_desc"]) if "tap_desc" in step else ("text", step.get("tap_text"))
    for node in ET.fromstring(ui_xml).iter("node"):
        if node.get(attribute) == value:
            x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds", "")))
            return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def ui_dump(adb):
    """Dumps the on-screen UI hierarchy.

    Args:
        adb: adb command prefix.

    Returns:
        The `uiautomator dump` XML, or "" when the dump failed.
    """
    subprocess.run(adb + ["shell", "uiautomator", "dump", UI_DUMP], capture_output=True)
    return subprocess.run(adb + ["exec-out", "cat", UI_DUMP], capture_output=True, text=True).stdout


def ui_signature(ui_xml):
    """Reduces a UI dump to what a scroll changes: each node's text, description and bounds.

    Args:
        ui_xml: `uiautomator dump` output.

    Returns:
        A tuple of (text, content-desc, bounds), or None when the dump is not valid XML.
    """
    try:
        nodes = ET.fromstring(ui_xml).iter("node")
        return tuple((n.get("text"), n.get("content-desc"), n.get("bounds")) for n in nodes)
    except ET.ParseError:
        return None


def gesture_moved(before, after):
    """Checks that a gesture changed the screen, from ui_signature() taken before and after it.

    Returns:
        "" when the screen changed, else the reason the measurement is inconclusive.
    """
    if before is None or after is None:
        return "could not dump the UI to confirm that the gesture moved the screen"
    return "" if before != after else "the gesture did not move the screen"


def open_screen(adb, package, entry):
    """Force-stops the app, then opens the screen by deep link, preview or steps.

    Args:
        adb: adb command prefix.
        package: application id.
        entry: screen map entry.

    Returns:
        An error message, or "" when the screen opened.
    """
    subprocess.run(adb + ["shell", "am", "force-stop", package], capture_output=True)
    command = launch_command(adb, package, entry)
    if command:
        start = subprocess.run(command, capture_output=True, text=True)
        output = (start.stdout + start.stderr).strip()
        return f"could not open {screen_label(entry)} in {package}: {output}" if "Error" in output else ""
    if not entry.get("steps"):
        return "the screen entry has no deeplink, preview or steps"
    subprocess.run(adb + ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)
    time.sleep(LAUNCH_SECONDS)
    for step in entry["steps"]:
        try:
            point = find_node(ui_dump(adb), step)
        except ET.ParseError:
            point = None
        if point is None:
            return f"step {json.dumps(step)} found no matching node in {package}"
        subprocess.run(adb + ["shell", "input", "tap", str(point[0]), str(point[1])], capture_output=True)
        time.sleep(STEP_SECONDS)
    return ""


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


def variant_apks(apks, build_task):
    """Keeps the APKs that an assemble task builds, by file name.

    Args:
        apks: APK paths.
        build_task: for example ":app:assembleFreeDebug", which builds app-free-debug.apk.

    Returns:
        The matching paths, or all of them when none match.
    """
    parts = build_task.strip(":").split(":")
    module = parts[-2] if len(parts) > 1 else ""
    variant = re.sub(r"(?<!^)([A-Z])", r"-\1", parts[-1].removeprefix("assemble")).lower()
    name = re.compile(rf"{re.escape(module)}-{re.escape(variant)}(-unsigned)?\.apk")
    matching = [apk for apk in apks if name.fullmatch(os.path.basename(apk))]
    return matching or apks


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
    apk = max(variant_apks(apks, build_task), key=os.path.getmtime)
    install = subprocess.run(adb + ["install", "-r", "-d", apk], capture_output=True, text=True)
    if "Success" not in install.stdout:
        return [f"Install failed: {os.path.relpath(apk, ROOT)}", (install.stdout + install.stderr).strip()]
    return []


def measure_screen(adb, package, entry, gesture, size, tags):
    """Opens one screen, waits for the counts to reset, performs one gesture and compares the counts.

    Args:
        adb: adb command prefix.
        package: application id.
        entry: screen map entry.
        gesture: one of GESTURES.
        size: (width, height) from screen_size().
        tags: tags expected on this screen.

    Returns:
        Failure lines: a count above MAX_RECOMPOSITIONS_ON_SCROLL, or "Inconclusive" when a tag
        logged nothing or the screen did not open.
    """
    label = screen_label(entry)
    if gesture not in GESTURES:
        return [f"Inconclusive: unknown gesture {gesture!r} for {', '.join(tags)}."]
    subprocess.run(adb + ["logcat", "-c"], capture_output=True)
    error = open_screen(adb, package, entry)
    if error:
        return [f"Inconclusive: {error}"]
    time.sleep(SETTLE_SECONDS)
    loaded = tracker_logs(adb)

    swipe = gesture_command(adb, gesture, *size)
    before = ui_signature(ui_dump(adb)) if swipe else None
    subprocess.run(adb + ["logcat", "-c"], capture_output=True)
    if swipe:
        subprocess.run(swipe, capture_output=True)
    time.sleep(GESTURE_SECONDS)
    during = tracker_logs(adb)
    if swipe:
        not_moved = gesture_moved(before, ui_signature(ui_dump(adb)))
        if not_moved:
            return [f"Inconclusive: on {label}, {not_moved}; counts not checked."]

    counts = parse_recomposition_counts(during)
    seen = parse_attached(loaded) | parse_attached(during) | parse_recomposition_counts(loaded).keys() | counts.keys()
    errors = []
    for tag in tags:
        if tag not in seen:
            errors.append(f"Inconclusive: no {TRACKER_TAG} log for {tag} on {label}; check that the screen opened.")
            continue
        info(f"{tag}: {counts.get(tag, 0)} recompositions during {gesture} on {label}")
        if counts.get(tag, 0) > MAX_RECOMPOSITIONS_ON_SCROLL:
            errors.append(f"{tag} recomposed {counts[tag]} times during {gesture} (max {MAX_RECOMPOSITIONS_ON_SCROLL}).")
    return errors


def measure_frames(adb, package, entry, gesture, repeats, size):
    """Opens one screen, resets gfxinfo, repeats the gesture and reads the frame stats.

    Args:
        adb: adb command prefix.
        package: application id.
        entry: screen map entry.
        gesture: one of GESTURES.
        repeats: how many times to perform the gesture.
        size: (width, height) from screen_size().

    Returns:
        (parse_gfxinfo result, error message or "").
    """
    error = open_screen(adb, package, entry)
    if error:
        return {}, error
    time.sleep(SETTLE_SECONDS)
    swipe = gesture_command(adb, gesture, *size)
    before = ui_signature(ui_dump(adb)) if swipe else None
    subprocess.run(adb + ["shell", "dumpsys", "gfxinfo", package, "reset"], capture_output=True)
    for _ in range(repeats):
        if swipe:
            subprocess.run(swipe, capture_output=True)
        time.sleep(GESTURE_SECONDS)
    output = subprocess.run(adb + ["shell", "dumpsys", "gfxinfo", package], capture_output=True, text=True).stdout
    if swipe:
        not_moved = gesture_moved(before, ui_signature(ui_dump(adb)))
        if not_moved:
            return {}, f"on {screen_label(entry)}, {not_moved}; frames not counted"
    return parse_gfxinfo(output), ""


def frame_verdict(label, runs, limits):
    """Summarises the frame runs of one screen and compares the medians with the limits.

    Args:
        label: screen name for messages.
        runs: parse_gfxinfo results, one per run.
        limits: {"max_janky_percent": float or None, "max_p95_ms": float or None}.

    Returns:
        (summary line, failure lines); the summary is None when no run has frame stats.
    """
    def spread(key):
        values = [run[key] for run in runs if key in run]
        if not values:
            return None, ""
        return statistics.median(values), f"{min(values)}–{max(values)}"

    janky, janky_range = spread("janky_percent")
    p95, p95_range = spread("p95")
    if janky is None or p95 is None:
        return None, [f"Inconclusive: gfxinfo returned no frame stats for {label}."]
    others = {key: spread(key)[0] for key in ("p50", "p90", "p99", "frames")}
    measured = sum("p95" in run for run in runs)
    summary = (f"frames on {label}: janky {janky}% ({janky_range}), p50 {others['p50']}ms, p90 {others['p90']}ms, "
               f"p95 {p95}ms ({p95_range}), p99 {others['p99']}ms, {others['frames']} frames; median of {measured} runs")
    failures = []
    if limits.get("max_janky_percent") is not None and janky > limits["max_janky_percent"]:
        failures.append(f"{label}: {janky}% janky frames (max {limits['max_janky_percent']}%).")
    if limits.get("max_p95_ms") is not None and p95 > limits["max_p95_ms"]:
        failures.append(f"{label}: p95 frame time {p95}ms (max {limits['max_p95_ms']}ms).")
    return summary, failures


def mapped_screens(ctx):
    """Reads the screen map and groups the tagged screens of the changed files.

    Args:
        ctx: check context; uses ctx.files.

    Returns:
        (screen map, {(label, gesture): (entry, [tags])}, "Inconclusive" lines).
    """
    tags = recomposition_tags(ctx.files)
    if not tags:
        return {}, {}, ['Inconclusive: no recomposeHighlighter("Tag") in the changed .kt files.']
    try:
        screen_map = json.loads(read_text(SCREEN_MAP))
    except ValueError:
        return {}, {}, [f"Inconclusive: {os.path.relpath(SCREEN_MAP, ROOT)} is missing or not valid JSON."]
    screens = screen_map.get("screens", {})
    errors = [f"Inconclusive: no entry for {tag} in config/recomposition_screens.json." for tag in sorted(tags - screens.keys())]
    by_screen = {}
    for tag in sorted(tags & screens.keys()):
        entry = screens[tag]
        if not (entry.get("deeplink") or entry.get("preview") or entry.get("steps")):
            errors.append(f"Inconclusive: no deeplink, preview or steps for {tag}.")
            continue
        key = (screen_label(entry), entry.get("gesture", "swipe_up"))
        by_screen.setdefault(key, (entry, []))[1].append(tag)
    return screen_map, by_screen, errors


def connected_adb(ctx):
    """Builds the adb prefix when the device is connected.

    Args:
        ctx: check context; uses ctx.device.

    Returns:
        (adb prefix or None, "Inconclusive" lines).
    """
    try:
        devices = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    except OSError:
        return None, ["Inconclusive: adb is not on PATH."]
    if f"{ctx.device}\tdevice" not in devices:
        return None, ["Inconclusive: no authorised device connected."]
    return ["adb"] + (["-s", ctx.device] if ctx.device else []), []


def check_recomposition(ctx):
    """Installs the debug build, opens each mapped screen and checks the recomposition count of each tag.

    Args:
        ctx: check context; uses ctx.files, ctx.device and ctx.skip_install.

    Returns:
        Failure lines; "Inconclusive" lines when a tag, the screen map, adb or the device is missing.
    """
    screen_map, by_screen, errors = mapped_screens(ctx)
    if not by_screen:
        return errors
    adb, missing = connected_adb(ctx)
    if not adb:
        return errors + missing
    if not ctx.skip_install:
        install_errors = install_build(adb, screen_map.get("build_task", DEFAULT_BUILD_TASK))
        if install_errors:
            return errors + install_errors
    size = screen_size(adb)
    for (label, gesture), (entry, tags) in by_screen.items():
        errors += measure_screen(adb, screen_map.get("package", ""), entry, gesture, size, tags)
    return errors


def check_frames(ctx):
    """Measures frame times on each mapped screen with gfxinfo and compares them with the limits.

    Uses gfx_build_task when it is set (installing it unless ctx.skip_install), else the build on the
    device. Run after check_recomposition, which installs the debug build.

    Args:
        ctx: check context; uses ctx.files, ctx.device and ctx.skip_install.

    Returns:
        Failure lines; "Inconclusive" lines when the screen cannot be measured.
    """
    screen_map, by_screen, errors = mapped_screens(ctx)
    if not by_screen:
        return errors
    adb, missing = connected_adb(ctx)
    if not adb:
        return errors + missing
    gfx_task = screen_map.get("gfx_build_task")
    if gfx_task and not ctx.skip_install:
        install_errors = install_build(adb, gfx_task)
        if install_errors:
            return errors + install_errors
    package, size = screen_map.get("package", ""), screen_size(adb)
    repeats = screen_map.get("gesture_repeats", DEFAULT_GESTURE_REPEATS)
    for (label, gesture), (entry, tags) in by_screen.items():
        if gfx_task and entry.get("preview"):
            errors.append(f"Inconclusive: {label} opens by preview, which {gfx_task} cannot run.")
            continue
        runs = []
        for _ in range(screen_map.get("frame_runs", DEFAULT_FRAME_RUNS)):
            stats, error = measure_frames(adb, package, entry, gesture, repeats, size)
            if error:
                errors.append(f"Inconclusive: {error}")
                break
            runs.append(stats)
        if runs:
            limits = {key: entry.get(key, screen_map.get(key)) for key in ("max_janky_percent", "max_p95_ms")}
            summary, failures = frame_verdict(label, runs, limits)
            if summary:
                info(summary)
            errors += failures
    return errors

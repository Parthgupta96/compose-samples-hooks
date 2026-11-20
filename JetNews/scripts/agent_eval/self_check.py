"""Assertions for the parsers and path rules. Run with `python3 scripts/agent_eval.py --self-check`."""
import os
import tempfile

from .common import ROOT, find_sdk, module_of, parse_hunks, parse_includes
from .checks import blocking
from .device import (find_node, frame_verdict, gesture_command, gesture_moved, launch_command, parse_attached,
                     parse_gfxinfo, parse_recomposition_counts, ui_signature, variant_apks)
from .hooks import GUARDED_PATHS
from .android_lint import lint_findings, parse_lint_xml, report_path
from .health import parse_anrs, parse_crashes, parse_strictmode
from .lint import AUTOCORRECTED, autocorrected, sarif_path
from .stability import (CLASS_DECL, COMPOSABLE_DECL, declarations, parse_stability_reports, report_files,
                        report_is_stale)


def self_check():
    """Runs every assertion; raises AssertionError on the first failure."""
    modules = ["app", "feature:api", "feature:impl", "feature"]
    assert module_of("feature/impl/src/A.kt", modules) == "feature:impl"
    assert module_of("feature/src/A.kt", modules) == "feature"
    assert module_of("appendix/A.kt", modules) is None
    groovy = "include ':app'\ninclude ':feature:api', ':feature:impl'\n//include ':old'\n"
    kts = 'include(":app")\ninclude(":core-data")\n// include(":old")\n'
    assert parse_includes(groovy) == ["app", "feature:api", "feature:impl"]
    assert parse_includes(kts) == ["app", "core-data"]

    assert ".claude/settings.local.json".startswith(GUARDED_PATHS)
    assert "scripts/agent_eval/hooks.py".startswith(GUARDED_PATHS)
    assert "config/detekt.yml".startswith(GUARDED_PATHS)
    assert not "scripts/other.py".startswith(GUARDED_PATHS)
    assert not "config/recomposition_screens.json".startswith(GUARDED_PATHS)

    # SDK lookup: local.properties, then the env, then adb's grandparent; only the last needs ANDROID_HOME set.
    sdk_dirs = {"/sdk/platforms", "/opt/sdk/platforms"}.__contains__
    assert find_sdk("sdk.dir=C\\:\\\\Android\n", {}, None, sdk_dirs) == ("C:\\Android", True)
    assert find_sdk("", {"ANDROID_SDK_ROOT": "/env/sdk"}, None, sdk_dirs) == ("/env/sdk", True)
    assert find_sdk("", {}, "/sdk/platform-tools/adb", sdk_dirs) == ("/sdk", False)
    assert find_sdk("", {}, None, lambda path: False) == (None, False)

    assert parse_hunks("@@ -3 +3 @@\n@@ -10,0 +11,2 @@\n@@ -20,4 +22,0 @@\n") == {3, 11, 12}
    assert sarif_path("file://" + ROOT + "/a%20b/C.kt") == "a b/C.kt" and sarif_path("x/C.kt") == "x/C.kt"

    report = "restartable skippable fun Card(\n  unstable items: List<String>\n  stable title: String\n)\n" \
             "restartable skippable fun Empty()\n"
    classes = "unstable class Model {\n}\nstable class Ok {\n}\nunstable class Model$$serializer {\n}\n"
    assert parse_stability_reports(report, classes) == ({"Card": ["items"]}, {"Model"})
    qualified = report.replace("fun Card(", "fun com.example.Card(")  # Kotlin 2.4+ report format
    assert parse_stability_reports(qualified, classes.replace("class Model {", "class com.example.Model {")) \
        == ({"Card": ["items"]}, {"Model"})
    with tempfile.TemporaryDirectory() as reports:
        assert report_files(reports) is None  # no report: the check says Inconclusive, not pass
        old, new = os.path.join(reports, "app-debug-composables.txt"), os.path.join(reports, "app-composables.txt")
        for path, mtime in ((old, 1), (new, 2)):
            open(path, "w").close()
            os.utime(path, (mtime, mtime))
        assert report_files(reports) == (new, os.path.join(reports, "app-classes.txt"))
        assert report_files(reports, "debug") == (old, os.path.join(reports, "app-debug-classes.txt"))
        source_file = os.path.join(reports, "A.kt")
        open(source_file, "w").close()
        os.utime(source_file, (3, 3))
        assert report_is_stale(new, [source_file])  # the agent edited after the last report
        os.utime(new, (4, 4))
        assert not report_is_stale(new, [source_file])
        assert report_is_stale(None, [source_file])
    assert parse_stability_reports("fun Card(\n  items: List<String>\n)\n", "") == ({"Card": []}, set())
    source = "@Composable\nprivate fun RowScope.Card(\n    items: List<String>,\n) {\n}\ndata class Model(val a: Int)\n"
    assert declarations(source, COMPOSABLE_DECL) == [("Card", 2, 4)]
    assert declarations(source, CLASS_DECL) == [("Model", 6, 6)]

    logcat = "D RecomposeTracker: Composable Row attached\nD RecomposeTracker: Composable Row count=1\n" \
             "D RecomposeTracker: Composable Row count=3\nD RecomposeTracker: Composable Card attached\n"
    assert parse_recomposition_counts(logcat) == {"Row": 3}
    assert parse_attached(logcat) == {"Row", "Card"}
    assert gesture_command(["adb"], "swipe_up", 1000, 2000) == ["adb", "shell", "input", "swipe", "500", "1400", "500", "600", "400"]
    assert gesture_command(["adb"], "none", 1000, 2000) is None

    assert launch_command(["adb"], "com.x", {"preview": "com.x.AKt.APreview"})[-4:] == \
        ["com.x/androidx.compose.ui.tooling.PreviewActivity", "--es", "composable", "com.x.AKt.APreview"]
    assert launch_command(["adb"], "com.x", {"deeplink": "https://x.com/a"})[-2:] == ["https://x.com/a", "com.x"]
    assert launch_command(["adb"], "com.x", {"steps": [{"tap_text": "A"}]}) is None
    ui = '<hierarchy><node text="" content-desc="Open menu" bounds="[0,78][123,201]"/>' \
         '<node text="History" content-desc="" bounds="[10,300][110,340]"/></hierarchy>'
    assert find_node(ui, {"tap_desc": "Open menu"}) == (61, 139)
    assert find_node(ui, {"tap_text": "History"}) == (60, 320)
    assert find_node(ui, {"tap_text": "Missing"}) is None
    scrolled = ui.replace("[10,300][110,340]", "[10,120][110,160]")
    assert gesture_moved(ui_signature(ui), ui_signature(scrolled)) == ""
    assert gesture_moved(ui_signature(ui), ui_signature(ui)) == "the gesture did not move the screen"
    assert ui_signature("ERROR: could not get idle state.") is None
    assert gesture_moved(ui_signature(ui), None).startswith("could not dump")

    gfx = "Total frames rendered: 240\nJanky frames: 12 (5.00%)\nJanky frames (legacy): 30 (12.50%)\n" \
          "50th percentile: 8ms\n90th percentile: 14ms\n95th percentile: 18ms\n99th percentile: 32ms\n" \
          "50th gpu percentile: 3ms\n95th gpu percentile: 5ms\n"
    assert parse_gfxinfo(gfx) == {"frames": 240, "janky": 12, "janky_percent": 5.0, "p50": 8, "p90": 14, "p95": 18, "p99": 32}
    runs = [parse_gfxinfo(gfx), {**parse_gfxinfo(gfx), "janky_percent": 9.0, "p95": 30}, parse_gfxinfo(gfx)]
    assert frame_verdict("S", runs, {"max_janky_percent": None, "max_p95_ms": None})[1] == []
    assert frame_verdict("S", runs, {"max_janky_percent": 4, "max_p95_ms": 17})[1] == \
        ["S: 5.0% janky frames (max 4%).", "S: p95 frame time 18ms (max 17ms)."]
    assert frame_verdict("S", [{}], {})[0] is None and frame_verdict("S", [{}], {})[1][0].startswith("Inconclusive")

    apks = ["app/build/outputs/apk/debug/app-debug.apk", "app/build/outputs/apk/benchmark/app-benchmark.apk",
            "app/build/outputs/apk/free/debug/app-free-debug.apk"]
    assert variant_apks(apks, ":app:assembleDebug") == [apks[0]]
    assert variant_apks(apks, ":app:assembleBenchmark") == [apks[1]]
    assert variant_apks(apks, ":app:assembleFreeDebug") == [apks[2]]
    assert blocking(["Inconclusive: no device", "Row recomposed 5 times"]) == ["Row recomposed 5 times"]
    assert blocking([AUTOCORRECTED + "A.kt:3 Preview should be private [compose:preview-public-check]"]) == []
    # A format pass shifts lines, so findings match on (file, message, rule); only the removed one is reported.
    before = [("A.kt", 3, "public preview", "compose:preview-public-check"), ("A.kt", 9, "mutable", "compose:mutable-params-check")]
    after = [("A.kt", 7, "mutable", "compose:mutable-params-check")]
    assert autocorrected(before, after) == [before[0]]
    assert autocorrected(after, after) == []
    # Android Lint: blocking severities on new files and changed lines only; version advice is dropped.
    lint_xml = (f'<issues><issue id="FrequentlyChangingValue" severity="Warning" message="scroll read">'
                f'<location file="{ROOT}/app/src/A.kt" line="24"/></issue>'
                f'<issue id="UnusedResources" severity="Warning" message="unused"><location file="{ROOT}/app/res/s.xml" line="9"/></issue>'
                f'<issue id="GradleDependency" severity="Warning" message="newer"><location file="{ROOT}/app/build.gradle.kts" line="3"/></issue>'
                f'<issue id="ModifierNodeInspectableProperties" severity="Hint" message="hint"><location file="{ROOT}/app/src/A.kt" line="5"/></issue>'
                f'<issue id="Other" severity="Error" message="old code"><location file="{ROOT}/app/src/Old.kt" line="7"/></issue></issues>')
    scope = {"app/src/A.kt": None, "app/res/s.xml": {8}, "app/build.gradle.kts": {3}, "app/src/Old.kt": {1}}
    assert lint_findings(parse_lint_xml(lint_xml), scope, {"GradleDependency"}) == \
        ["app/src/A.kt:24 scroll read [FrequentlyChangingValue]"]
    assert report_path("feature:impl", "lintFreeDebug").endswith("feature/impl/build/reports/lint-results-freeDebug.xml")

    # Crashes and ANRs of the app only; StrictMode only when a frame is in an edited file.
    log = ("11-20 06:35:08.096  9817  9817 E AndroidRuntime: FATAL EXCEPTION: main\n"
           "11-20 06:35:08.096  9817  9817 E AndroidRuntime: Process: com.x, PID: 9817\n"
           "11-20 06:35:08.096  9817  9817 E AndroidRuntime: java.io.FileNotFoundException: probe\n"
           "11-20 06:35:08.096  9817  9817 E AndroidRuntime: \tat com.x.ui.AKt.A(A.kt:12)\n"
           "11-20 06:35:09.000   900   950 E ActivityManager: ANR in com.x (com.x/.Main)\n"
           "11-20 06:35:09.000   900   950 E ActivityManager: ANR in com.xy (com.xy/.Main)\n"
           "11-20 06:34:14.310  9571  9571 D StrictMode: StrictMode policy violation; ~duration=5 ms: android.os.strictmode.DiskReadViolation\n"
           "11-20 06:34:14.310  9571  9571 D StrictMode: \tat java.io.File.length(File.java:984)\n"
           "11-20 06:34:14.310  9571  9571 D StrictMode: \tat com.x.JetApp.onCreate(JetApp.kt:32)\n"
           "11-20 06:34:15.310  9571  9571 D StrictMode: StrictMode policy violation; ~duration=2 ms: android.os.strictmode.DiskReadViolation\n"
           "11-20 06:34:15.310  9571  9571 D StrictMode: \tat com.x.ui.interests.InterestsScreenKt.InterestsScreen(InterestsScreen.kt:147)\n"
           "11-20 06:34:15.310  9571  9571 D StrictMode: \tat com.x.ui.interests.InterestsScreenKt.entry(InterestsScreen.kt:124)\n")
    assert parse_crashes(log, "com.x") == ["The app crashed: java.io.FileNotFoundException: probe (at com.x.ui.AKt.A(A.kt:12))"]
    wrapped = ("E AndroidRuntime: FATAL EXCEPTION: main\nE AndroidRuntime: Process: com.x, PID: 1\n"
               "E AndroidRuntime: java.lang.RuntimeException: java.lang.reflect.InvocationTargetException\n"
               "E AndroidRuntime: \tat com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:614)\n"
               "E AndroidRuntime: Caused by: java.io.FileNotFoundException: missing\n"
               "E AndroidRuntime: \tat java.io.FileInputStream.open(FileInputStream.java:1)\n"
               "E AndroidRuntime: \tat com.x.ui.RowKt.Row(Row.kt:189)\n")
    assert parse_crashes(wrapped, "com.x", ["app/src/main/java/com/x/ui/Row.kt"]) == \
        ["The app crashed: java.io.FileNotFoundException: missing (app/src/main/java/com/x/ui/Row.kt:189)"]
    assert parse_crashes(wrapped, "com.x") == ["The app crashed: java.io.FileNotFoundException: missing (at com.x.ui.RowKt.Row(Row.kt:189))"]
    assert parse_crashes(log, "com.other") == []
    assert len(parse_anrs(log, "com.x")) == 1
    edited = ["app/src/main/java/com/x/ui/interests/InterestsScreen.kt"]
    assert parse_strictmode(log, edited) == \
        ["StrictMode DiskReadViolation at app/src/main/java/com/x/ui/interests/InterestsScreen.kt:147. Move this work off the main thread."]
    assert parse_strictmode(log, ["app/src/main/java/com/y/ui/interests/InterestsScreen.kt"]) == []  # same name, other package
    print("self-check ok")

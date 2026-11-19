"""Assertions for the parsers and path rules. Run with `python3 scripts/agent_eval.py --self-check`."""
import os
import tempfile

from .common import ROOT, module_of, parse_hunks, parse_includes
from .checks import blocking
from .device import (find_node, frame_verdict, gesture_command, gesture_moved, launch_command, parse_attached,
                     parse_gfxinfo, parse_recomposition_counts, ui_signature, variant_apks)
from .hooks import GUARDED_PATHS
from .lint import sarif_path
from .stability import CLASS_DECL, COMPOSABLE_DECL, declarations, parse_stability_reports, report_files


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
    assert frame_verdict("S", [{}], {})[1][0].startswith("Inconclusive")

    apks = ["app/build/outputs/apk/debug/app-debug.apk", "app/build/outputs/apk/benchmark/app-benchmark.apk",
            "app/build/outputs/apk/free/debug/app-free-debug.apk"]
    assert variant_apks(apks, ":app:assembleDebug") == [apks[0]]
    assert variant_apks(apks, ":app:assembleBenchmark") == [apks[1]]
    assert variant_apks(apks, ":app:assembleFreeDebug") == [apks[2]]
    assert blocking(["Inconclusive: no device", "Row recomposed 5 times"]) == ["Row recomposed 5 times"]
    print("self-check ok")

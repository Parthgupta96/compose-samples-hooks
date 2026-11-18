"""Assertions for the parsers and path rules. Run with `python3 scripts/agent_eval.py --self-check`."""
from .common import ROOT, module_of, parse_hunks, parse_includes
from .device import gesture_command, parse_attached, parse_recomposition_counts
from .hooks import GUARDED_PATHS
from .lint import sarif_path
from .stability import CLASS_DECL, COMPOSABLE_DECL, declarations, parse_stability_reports


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

    assert parse_hunks("@@ -3 +3 @@\n@@ -10,0 +11,2 @@\n@@ -20,4 +22,0 @@\n") == {3, 11, 12}
    assert sarif_path("file://" + ROOT + "/a%20b/C.kt") == "a b/C.kt" and sarif_path("x/C.kt") == "x/C.kt"

    report = "restartable skippable fun Card(\n  unstable items: List<String>\n  stable title: String\n)\n" \
             "restartable skippable fun Empty()\n"
    classes = "unstable class Model {\n}\nstable class Ok {\n}\nunstable class Model$$serializer {\n}\n"
    assert parse_stability_reports(report, classes) == ({"Card": ["items"]}, {"Model"})
    qualified = report.replace("fun Card(", "fun com.example.Card(")  # Kotlin 2.4+ report format
    assert parse_stability_reports(qualified, classes.replace("class Model {", "class com.example.Model {")) \
        == ({"Card": ["items"]}, {"Model"})
    source = "@Composable\nprivate fun RowScope.Card(\n    items: List<String>,\n) {\n}\ndata class Model(val a: Int)\n"
    assert declarations(source, COMPOSABLE_DECL) == [("Card", 2, 4)]
    assert declarations(source, CLASS_DECL) == [("Model", 6, 6)]

    logcat = "D RecomposeTracker: Composable Row attached\nD RecomposeTracker: Composable Row count=1\n" \
             "D RecomposeTracker: Composable Row count=3\nD RecomposeTracker: Composable Card attached\n"
    assert parse_recomposition_counts(logcat) == {"Row": 3}
    assert parse_attached(logcat) == {"Row", "Card"}
    assert gesture_command(["adb"], "swipe_up", 1000, 2000) == ["adb", "shell", "input", "swipe", "500", "1400", "500", "600", "400"]
    assert gesture_command(["adb"], "none", 1000, 2000) is None
    print("self-check ok")

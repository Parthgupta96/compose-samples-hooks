# Agent eval kit — setup

Deterministic checks that run as Claude Code hooks on the code an agent writes. A failing check
sends its report back to the agent, with at most 3 fix rounds per turn.

| Check | Trigger | Scope |
|---|---|---|
| ktlint + Compose rules | Stop | New Kotlin files: formatted, every rule. Old files: Compose rules on changed lines |
| detekt | Stop | New files: every line. Old files: changed lines |
| Compile | Stop | `compile_task` of each module that owns an edited file |
| Compose stability | Stop, after the compile | Unstable parameters of edited composables; unstable classes in edited `*UIModel.kt` |
| Recomposition on a device | Manual: `--stage device` | Tagged composables, max 2 recompositions per gesture |
| Guard | Before each Edit / Write | Asks the user before an edit to a kit file |

Requirements: Python 3, Java 17 or later, git. The device stage also needs `adb`.

## 1. Copy the kit

Paste the contents of this folder into the root of the Gradle project (the folder that holds
`settings.gradle(.kts)` and `gradlew`):

```
.claude/settings.json
scripts/agent_eval.py
scripts/agent_eval/
config/agent_eval.json
config/detekt.yml
config/ktlint.editorconfig
config/recomposition_screens.json
```

If the project already has `.claude/settings.json`, merge the four `hooks` entries into it.

## 2. Install the linters

```bash
python3 scripts/agent_eval.py --install-tools
```

This downloads pinned ktlint 1.8.0, compose-rules 0.6.8 and detekt 1.23.8 (about 206 MB) to
`build/guardrail-tools/` and verifies each SHA-256. `build/` must be gitignored.

## 3. Set `config/agent_eval.json`

| Key | Meaning | Example |
|---|---|---|
| `compile_task` | Kotlin compile task name, run per module | `compileDebugKotlin`, or `compileFreeDebugKotlin` with flavors |
| `report_variant` | Variant part of the Compose report file names | `debug`, or `freeDebug` |
| `skip_compile_modules` | Modules that do not have `compile_task` | `["lint-rules"]` |
| `device_in_stop` | Also run the device checks (section 6) in the Stop hook | `false` (default), `true` |

Find the task names with `./gradlew :app:tasks --all | grep -E '^compile.*Kotlin'`.

## 4. Turn on Compose compiler reports

Add this block to the root build file. The check reads the reports after its compile.

`build.gradle.kts`:

```kotlin
subprojects {
    plugins.withId("org.jetbrains.kotlin.plugin.compose") {
        if (project.hasProperty("enableComposeReports")) {
            extensions.configure<org.jetbrains.kotlin.compose.compiler.gradle.ComposeCompilerGradlePluginExtension> {
                reportsDestination.set(layout.buildDirectory.dir("compose_compiler"))
                metricsDestination.set(layout.buildDirectory.dir("compose_compiler"))
            }
        }
    }
}
```

`build.gradle`:

```groovy
subprojects {
    plugins.withId('org.jetbrains.kotlin.plugin.compose') {
        if (project.hasProperty('enableComposeReports')) {
            project.composeCompiler {
                reportsDestination = project.layout.buildDirectory.dir('compose_compiler')
                metricsDestination = project.layout.buildDirectory.dir('compose_compiler')
            }
        }
    }
}
```

The Kotlin DSL version needs the Compose compiler Gradle plugin on the root build classpath. Most
projects already declare it in the root `plugins {}` block with `apply false`.

Check: `./gradlew :app:<compile_task> -PenableComposeReports` writes files to
`app/build/compose_compiler/`.

## 5. Verify

```bash
python3 scripts/agent_eval.py --self-check
```

```bash
python3 scripts/agent_eval.py
```

The second command runs the Stop checks on the git working tree.

## 6. Device checks (optional)

`python3 scripts/agent_eval.py --stage device` installs the app, opens each tagged screen and swipes it. It runs two
checks:

- **Recomposition:** the highest `count=` per tag during one swipe must be 2 or less.
- **Frames:** `dumpsys gfxinfo` after `gesture_repeats` swipes, `frame_runs` times. It prints the median janky % and
  the p50/p90/p95/p99 frame times. It fails only when `max_janky_percent` or `max_p95_ms` is set and the median is
  above it.

The recomposition check reads logcat lines with the tag `RecomposeTracker`:

- `Composable <Tag> attached` when a tagged node first appears;
- `Composable <Tag> count=<n>` on each recomposition, with the count reset after about 3 s idle.

Add a debug-only `Modifier.recomposeHighlighter(tag)` that logs these lines. Google's public
recompose-highlighter snippet is a good base: log `attached` in `onAttach()` and `count=` where it
increments its counter.

Tag the root of each new list row, and each screen root, with `Modifier.recomposeHighlighter("<Name>")`. Then map each
tag in `config/recomposition_screens.json`. A screen opens in one of three ways:

| Entry | Opens | Notes |
|---|---|---|
| `"deeplink": "https://…"` | the full page by deep link | Best when the app has deep links |
| `"steps": [{"tap_desc": "…"}, {"tap_text": "…"}]` | the full page: launches the app, then taps each node found by content description or text | Breaks when the UI text changes |
| `"preview": "com.example.FooKt.FooPreview"` | the `@Preview` through ui-tooling's `PreviewActivity` | Debug builds only; no app scaffold, drawer or real insets |

Each entry can also set `gesture` (`swipe_up` by default, `swipe_down` or `none`) and its own `max_janky_percent` or
`max_p95_ms`. The top-level keys are:

- `package` and `build_task`, which must name the same debug variant;
- `gfx_build_task`, which is optional, for example a non-debuggable `:app:assembleBenchmark`. Frames are then measured
  on that build, which cannot open a preview;
- `gesture_repeats`, `frame_runs`, and global limits.

Debug builds have slow frame times, so measure frames on a non-debuggable build when one exists.

With `device_in_stop: true`, the Stop hook runs both checks after the other checks. A missing device, tag or map
entry never blocks; only a count or frame time over its limit does. Each Stop with a tagged file then builds and
installs the app, and that adds about a minute or more.

## Day-to-day

- The Stop hook runs on its own. Fix every finding.
- Do not edit the kit files or add suppressions to make a check pass; the guard asks the user first.
- After ktlint formats a new file, read the file again before the next edit.

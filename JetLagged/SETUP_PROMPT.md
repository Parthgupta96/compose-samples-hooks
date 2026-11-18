Set up the agent eval kit in this project. The kit files are already in this folder. Do the steps
in order, and stop and tell me if a step fails.

1. Read `SETUP.md` in full.
2. Find the Gradle project root (the folder with `settings.gradle(.kts)` and `gradlew`). If it is not
   the current folder, tell me and stop.
3. List the Kotlin compile tasks of the app module:
   `./gradlew :app:tasks --all | grep -E '^compile.*Kotlin'`.
   Set `config/agent_eval.json`: `compile_task` (the main, non-test debug task), `report_variant`
   (the variant part of that task name, for example `debug`), and `skip_compile_modules` (modules from
   the settings file that have no such task).
4. Add the Compose reports block from SETUP.md section 4 to the root build file, in the file's DSL.
   Run `./gradlew :app:<compile_task> -PenableComposeReports` and confirm that
   `app/build/compose_compiler/` now has a `*-composables.txt` file.
5. Check that `build/` is in `.gitignore`. Add it if it is missing.
6. Ask me before you run `python3 scripts/agent_eval.py --install-tools`. It downloads about 206 MB
   from GitHub. Run it after I agree.
7. Run `python3 scripts/agent_eval.py --self-check`.
8. Prove the Stop checks work:
   a. Create `app/src/main/java/KitProbe.kt` with this content:
      `fun kitProbe(): Int = "not an int"`
   b. Run `python3 scripts/agent_eval.py --module app` and confirm it exits 1 with a compile error.
   c. Delete the file and run the same command again; confirm it passes.
9. Commit only the kit files, the build file change, `.gitignore` and `config/agent_eval.json`,
   with the message: `Add agent eval kit`.
10. Report: the values you put in `config/agent_eval.json`, the result of each step, and the
    commit hash.

Do not change any other source file.

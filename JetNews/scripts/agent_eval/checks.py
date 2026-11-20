"""Check registry. A new check is one function `check(ctx) -> list[str]` plus one CHECKS row.

ctx carries files (repo-relative paths), device (adb serial or "") and skip_install (bool).
An empty list means the check passed.
"""
from types import SimpleNamespace

from .android_lint import check_android_lint
from .build import check_compile
from .common import load_settings
from .device import check_frames, check_recomposition, check_release_smoke
from .lint import AUTOCORRECTED, check_detekt, check_ktlint
from .stability import check_compose_stability

# Runs in this order; check_compose_stability reads the reports that check_compile writes.
CHECKS = [
    (check_ktlint, {"stop", "manual"}),
    (check_detekt, {"stop", "manual"}),
    (check_compile, {"stop", "manual"}),
    (check_compose_stability, {"stop", "manual"}),
    (check_android_lint, {"stop", "manual"}),
    (check_recomposition, {"device"}),
    (check_frames, {"device"}),
    (check_release_smoke, {"release"}),
]


def blocking(lines):
    """Drops the lines that must not block a Stop.

    "Inconclusive" lines (a missing device, tag, report or SDK) and "Autocorrected" lines (ktlint already
    fixed the file) are reported by --stage manual but never block.
    """
    return [line for line in lines if not line.startswith(("Inconclusive", AUTOCORRECTED))]


def check_device_in_stop(ctx):
    """Stop stage: the recomposition and frame checks, when device_in_stop is on in config/agent_eval.json.

    Args:
        ctx: check context.

    Returns:
        Failure lines; empty when device_in_stop is off. run_checks drops the "Inconclusive" ones.
    """
    if not load_settings()["device_in_stop"]:
        return []
    return check_recomposition(ctx) + check_frames(ctx)


# Last, so a Stop compiles and lints before it spends time on the device.
CHECKS.append((check_device_in_stop, {"stop"}))


def run_checks(stage, files, device="", skip_install=False):
    """Runs every check registered for a stage.

    Args:
        stage: "manual", "stop", "device" or "release".
        files: repo-relative paths to check.
        device: adb serial; empty for the only connected device.
        skip_install: device stage only; use the build already on the device.

    Returns:
        One text block per failed check, headed by the check name.
    """
    ctx = SimpleNamespace(files=files, device=device, skip_install=skip_install)
    failures = []
    for check, stages in CHECKS:
        if stage in stages:
            errors = check(ctx)
            if stage == "stop":
                errors = blocking(errors)
            if errors:
                failures.append(f"[{check.__name__}]\n" + "\n".join(f"  {e}" for e in errors))
    return failures

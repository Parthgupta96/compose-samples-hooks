"""Check registry. A new check is one function `check(ctx) -> list[str]` plus one CHECKS row.

ctx carries files (repo-relative paths), device (adb serial or "") and skip_install (bool).
An empty list means the check passed.
"""
from types import SimpleNamespace

from .build import check_compile
from .device import check_recomposition
from .lint import check_detekt, check_ktlint
from .stability import check_compose_stability

# Runs in this order; check_compose_stability reads the reports that check_compile writes.
CHECKS = [
    (check_ktlint, {"stop", "manual"}),
    (check_detekt, {"stop", "manual"}),
    (check_compile, {"stop", "manual"}),
    (check_compose_stability, {"stop", "manual"}),
    (check_recomposition, {"device"}),
]


def run_checks(stage, files, device="", skip_install=False):
    """Runs every check registered for a stage.

    Args:
        stage: "manual", "stop" or "device".
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
            if errors:
                failures.append(f"[{check.__name__}]\n" + "\n".join(f"  {e}" for e in errors))
    return failures

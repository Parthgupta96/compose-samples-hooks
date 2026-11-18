"""Pinned linter downloads in build/guardrail-tools and a runner for linters that write report files."""
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request

from .common import ROOT, read_text, remove

TOOLS_DIR = os.path.join(ROOT, "build", "guardrail-tools")
TOOL_TIMEOUT_SECONDS = 300
KTLINT = "ktlint"
COMPOSE_RULES = "ktlint-compose-0.6.8-all.jar"
DETEKT = "detekt-cli-1.23.8-all.jar"
TOOLS = {
    KTLINT: (
        "https://github.com/ktlint/ktlint/releases/download/1.8.0/ktlint",
        "a3fd620207d5c40da6ca789b95e7f823c54e854b7fade7f613e91096a3706d75",
    ),
    COMPOSE_RULES: (
        "https://github.com/mrmans0n/compose-rules/releases/download/v0.6.8/ktlint-compose-0.6.8-all.jar",
        "a25378ec616add11d2b279a87f54ccffefea87917da13773ff753386d30c22e5",
    ),
    # The detekt release publishes no checksum; this is the hash of the first verified download.
    DETEKT: (
        "https://github.com/detekt/detekt/releases/download/v1.23.8/detekt-cli-1.23.8-all.jar",
        "2ce2ff952e150baf28a29cda70a363b0340b3e81a55f43e51ec5edffc3d066c1",
    ),
}


def tool(name):
    """Finds an installed tool.

    Args:
        name: a key of TOOLS.

    Returns:
        The absolute path, or None when --install-tools has not installed it.
    """
    path = os.path.join(TOOLS_DIR, name)
    return path if os.path.exists(path) else None


def install_tools():
    """Downloads each missing tool and verifies its SHA-256.

    A file with a wrong checksum is deleted and the process exits with an error.
    """
    os.makedirs(TOOLS_DIR, exist_ok=True)
    for name, (url, sha256) in TOOLS.items():
        path = os.path.join(TOOLS_DIR, name)
        if os.path.exists(path):
            print(f"present: {name}")
            continue
        print(f"downloading: {url}")
        partial = path + ".partial"
        urllib.request.urlretrieve(url, partial)
        with open(partial, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != sha256:
            remove(partial)
            sys.exit(f"checksum mismatch for {name}: expected {sha256}, got {actual}")
        os.replace(partial, path)
        print(f"installed: {name}")


def run_tool(command, report_suffix):
    """Runs a linter from the repo root and collects its report file.

    Args:
        command: argument list; the "{report}" placeholder is replaced with a temporary path.
        report_suffix: file suffix for the temporary report, for example ".json".

    Returns:
        (report text, combined stdout and stderr). The report text is None when the tool wrote
        no report or timed out.
    """
    handle, report = tempfile.mkstemp(suffix=report_suffix)
    os.close(handle)
    try:
        result = subprocess.run(
            [arg.replace("{report}", report) for arg in command],
            cwd=ROOT, capture_output=True, text=True, timeout=TOOL_TIMEOUT_SECONDS,
        )
        return read_text(report) or None, result.stderr + result.stdout
    except subprocess.TimeoutExpired:
        return None, f"Timed out after {TOOL_TIMEOUT_SECONDS}s: {command[2]}"
    finally:
        remove(report)


def tool_failure(name, output):
    """Formats the failure lines for a linter that wrote no report.

    Args:
        name: tool name for the message.
        output: combined stdout and stderr.

    Returns:
        A heading plus the last 10 meaningful output lines; JVM warnings and stack frames are dropped.
    """
    lines = [line for line in output.splitlines() if line.strip() and not line.startswith(("WARNING", "\tat "))]
    return [f"{name} produced no report:"] + lines[-10:]

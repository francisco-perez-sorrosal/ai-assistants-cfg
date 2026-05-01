"""Starter architectural invariant: pre-commit (check_*) scripts must not import post-merge (finalize_*) scripts.

Cites: CLAUDE.md§Structural Beauty (reliable systems are beautiful ones — well-organized code
with clean boundaries and cohesive modules signals structural soundness; mixing
pre-commit and post-merge execution contexts is a structural smell that this
invariant prevents).

This test runs the import-linter contract `check-scripts-precondition-boundary` declared
in `fitness/import-linter.cfg` and asserts it KEEPS (passes). The implementer of
Step 2.3 replaces the placeholder contract with this real invariant contract; this
test verifies the wiring holds end-to-end.
"""

import subprocess
from pathlib import Path



def test_starter_invariant_holds(project_root: Path, import_linter_cfg: Path) -> None:
    """The starter contract MUST pass — run import-linter via subprocess."""
    result = subprocess.run(
        ["uv", "run", "lint-imports", "--config", str(import_linter_cfg)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    # exit 0 = all contracts KEPT; non-zero = at least one BROKEN or config error
    assert result.returncode == 0, (
        f"Fitness contract failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

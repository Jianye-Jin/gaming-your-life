from __future__ import annotations
import os
import subprocess
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    p = start
    for _ in range(8):
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    # fallback to home (should not happen)
    return start


def main() -> int:
    here = Path(__file__).resolve()
    repo_root = find_repo_root(here)
    app_path = repo_root / "src" / "fate_app" / "app.py"

    port = os.environ.get("FATE_PORT", "8501")
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

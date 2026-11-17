"""Writes .env from .env.example and replaces every CHANGE_ME with a random secret.

uv run python scripts/init_env.py           # refuses to overwrite an existing .env
uv run python scripts/init_env.py --force
"""

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    target = ROOT / ".env"
    if target.exists() and "--force" not in sys.argv:
        print(".env exists – use --force to overwrite")
        return 1
    lines = []
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        lines.append(line.replace("CHANGE_ME", secrets.token_urlsafe(24)))
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o600)
    print(
        "written: .env (secrets generated; the administrator password is BOOTSTRAP_ADMIN_PASSWORD)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

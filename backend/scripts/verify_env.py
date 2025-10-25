from __future__ import annotations

import sys

from ..app.core.config import get_settings

REQUIRED = [
    "jwt_secret",
]


def main() -> int:
    settings = get_settings()
    missing = []
    for field in REQUIRED:
        if not getattr(settings, field):
            missing.append(field)
    if missing:
        print(f"Missing critical configuration values: {', '.join(missing)}")
        return 1
    print("Environment configuration looks good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Element codes like RO-019."""

import re


def next_code(existing: list[str], prefix: str) -> str:
    numbers = [
        int(m.group(1)) for c in existing if (m := re.fullmatch(rf"{re.escape(prefix)}-(\d+)", c))
    ]
    return f"{prefix}-{(max(numbers) if numbers else 0) + 1:03d}"


def full_name(first_name: str, last_name: str) -> str:
    return " ".join(x.strip() for x in (first_name, last_name) if x.strip())

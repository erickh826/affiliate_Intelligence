from __future__ import annotations

import sys
from pathlib import Path

from mdx_safety import mdx_syntax_issues, strip_frontmatter

_CONTENT_ROOT = Path(__file__).resolve().parents[2] / "apps" / "web" / "content"


def content_mdx_failures(root: Path = _CONTENT_ROOT) -> list[tuple[Path, str]]:
    """Return content MDX files whose body would fail the quality gate."""
    failures: list[tuple[Path, str]] = []
    if not root.exists():
        return [(root, "content directory is missing")]
    paths = sorted(path for path in root.rglob("*.mdx") if path.is_file())
    if not paths:
        return [(root, "no MDX files found")]
    for path in paths:
        issues = mdx_syntax_issues(strip_frontmatter(path.read_text(encoding="utf-8")))
        if issues:
            failures.append((path, issues[0]))
    return failures


def main() -> int:
    """Exit 1 when any published article would fail MDX checks."""
    failures = content_mdx_failures()
    if failures:
        for path, issue in failures:
            print(f"{path}: {issue}")
        print(f"{len(failures)} MDX file(s) failed the syntax check")
        return 1
    root = _CONTENT_ROOT
    count = len(list(root.rglob("*.mdx"))) if root.exists() else 0
    print(f"MDX syntax check passed ({count} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

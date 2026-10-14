from __future__ import annotations

import re

_APPROVED_COMPONENTS = frozenset({"AffiliateCTA", "Image"})
_APPROVED_COMPONENT_RE = re.compile(
    r"<(?:AffiliateCTA|Image)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*?/>",
    re.DOTALL,
)
_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)\b[^>]*>", re.DOTALL)
_LINK_RE = re.compile(r"\[([^\]\n]*)\](\([^)\n]*\))")
_PLACEHOLDER_RE = re.compile(r"\{\{(?:LINK|IMAGE)_[A-Z0-9_]+\}\}")
_IMAGE_PLACEHOLDER_RE = re.compile(r"\{\{IMAGE_[A-Z0-9_]+\}\}")
_LINK_PLACEHOLDER_RE = re.compile(r"\{\{LINK_[A-Z0-9_]+\}\}")
_LITERAL_LT_NEXT = frozenset(" \t\r\n")


def sanitize_mdx(text: str) -> str:
    """Escape MDX that would crash compilation, leaving code and components."""
    return "".join(
        chunk if kind == "keep" else _escape_plain(chunk)
        for kind, chunk in _regions(text)
    )


def prepare_written_mdx(text: str) -> str:
    """Escape unsafe MDX and drop placeholders MDX would execute as JavaScript."""
    parts: list[str] = []
    for kind, chunk in _regions(sanitize_mdx(text)):
        if kind == "keep":
            parts.append(chunk)
            continue
        plain = _IMAGE_PLACEHOLDER_RE.sub("", chunk)
        parts.append(_LINK_PLACEHOLDER_RE.sub(_escape_link_placeholder, plain))
    return "".join(parts)


def mdx_syntax_issues(text: str) -> list[str]:
    """Return MDX problems that should fail the quality gate."""
    for kind, chunk in _regions(text):
        if kind != "plain":
            continue
        issues = _issues_in_plain(chunk)
        if issues:
            return issues
    return []


def strip_frontmatter(text: str) -> str:
    """Return MDX body, leaving text unchanged when frontmatter is absent."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "".join(lines[index + 1 :])
    return text


def _regions(text: str) -> list[tuple[str, str]]:
    regions: list[tuple[str, str]] = []
    index = 0
    length = len(text)
    while index < length:
        if text.startswith("```", index):
            closing = text.find("```", index + 3)
            if closing == -1:
                regions.append(("keep", text[index:]))
                break
            regions.append(("keep", text[index : closing + 3]))
            index = closing + 3
            continue
        if text[index] == "`":
            closing = text.find("`", index + 1)
            if closing != -1 and "\n" not in text[index + 1 : closing]:
                regions.append(("keep", text[index : closing + 1]))
                index = closing + 1
                continue
        component = _APPROVED_COMPONENT_RE.match(text, index)
        if component:
            regions.append(("keep", component.group(0)))
            index = component.end()
            continue
        link = _LINK_RE.match(text, index)
        if link:
            regions.append(("plain", "["))
            regions.append(("plain", link.group(1)))
            regions.append(("plain", "]"))
            regions.append(("keep", link.group(2)))
            index = link.end()
            continue
        end = _next_boundary(text, index + 1)
        regions.append(("plain", text[index:end]))
        index = end
    return regions


def _next_boundary(text: str, start: int) -> int:
    length = len(text)
    index = start
    while index < length:
        if text.startswith("```", index) or text[index] in "`[":
            return index
        if text[index] == "<" and _APPROVED_COMPONENT_RE.match(text, index):
            return index
        index += 1
    return length


def _is_escaped(text: str, index: int) -> bool:
    slashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        slashes += 1
        cursor -= 1
    return slashes % 2 == 1


def _escape_plain(text: str) -> str:
    parts: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if _is_escaped(text, index):
            parts.append(text[index])
            index += 1
            continue
        placeholder = _PLACEHOLDER_RE.match(text, index)
        if placeholder:
            parts.append(placeholder.group(0))
            index = placeholder.end()
            continue
        if text[index] == "<":
            if index + 1 < length and text[index + 1] in _LITERAL_LT_NEXT:
                parts.append("<")
                index += 1
                continue
            tag = _TAG_RE.match(text, index)
            if tag:
                parts.append(tag.group(0))
                index = tag.end()
                continue
            parts.append("\\<")
            index += 1
            continue
        if text[index] in "{}":
            parts.append("\\" + text[index])
            index += 1
            continue
        parts.append(text[index])
        index += 1
    return "".join(parts)


def _issues_in_plain(text: str) -> list[str]:
    for match in _TAG_RE.finditer(text):
        component = match.group(1)
        tag = match.group(0)
        if component not in _APPROVED_COMPONENTS:
            return [f"raw or unapproved tag found: {_preview(tag)}"]
        if tag.startswith("</") or not tag.endswith("/>"):
            return [f"approved component must be self-closing: {_preview(tag)}"]
    consumed = [match.span() for match in _TAG_RE.finditer(text)]
    index = 0
    while index < len(text):
        if any(start <= index < end for start, end in consumed):
            index += 1
            continue
        placeholder = _PLACEHOLDER_RE.match(text, index)
        if placeholder and not _is_escaped(text, index):
            index = placeholder.end()
            continue
        char = text[index]
        if char == "<" and not _is_escaped(text, index):
            nxt = text[index + 1] if index + 1 < len(text) else ""
            if nxt not in _LITERAL_LT_NEXT:
                return [f"MDX-unsafe '<': {_preview(text[index:])}"]
        if char in "{}" and not _is_escaped(text, index):
            return [f"unescaped brace in MDX: {_preview(text[max(0, index - 8):])}"]
        index += 1
    return []


def _escape_link_placeholder(match: re.Match[str]) -> str:
    name = match.group(0)[2:-2]
    return "\\{\\{" + name + "\\}\\}"


def _preview(text: str) -> str:
    line = text.splitlines()[0] if text else ""
    if len(line) <= 80:
        return line
    return line[:77] + "..."

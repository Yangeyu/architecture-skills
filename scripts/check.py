#!/usr/bin/env python3
"""Check this repository's skill metadata and local Markdown references."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("architecture-co-design", "structure-expression")


def check_metadata(path, text):
    errors = []
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        return ["missing frontmatter boundaries"]
    metadata = match.group(1)
    names = re.findall(r"^name:\s*([^\n]+)$", metadata, re.MULTILINE)
    if names != [path.parent.name]:
        errors.append("name must match the skill directory")
    if not re.search(r"^description:\s*\S", metadata, re.MULTILINE):
        errors.append("missing description")
    if re.search(r"^description:\s*[>|][-+]?\s*$", metadata, re.MULTILINE):
        if not re.search(r"^description:.*\n[ \t]+\S", metadata, re.MULTILINE):
            errors.append("empty multiline description")
    for key in ("disable-model-invocation", "user-invocable"):
        values = re.findall(rf"^{key}:\s*(true|false)\s*$", metadata, re.MULTILINE)
        if len(values) != 1:
            errors.append(f"expected one boolean {key}")
    return errors


def check_markdown(path, text):
    errors = []
    if not text.strip() or not text.endswith("\n"):
        errors.append("empty document or missing final newline")
    if any(ord(char) < 32 and char not in "\n\t" for char in text):
        errors.append("unexpected control character")
    if "[118;1:3u" in text:
        errors.append("terminal escape artifact")

    fence = None
    prose = []
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence is None and marker:
            fence = marker.group(1)
        elif fence is not None:
            if marker:
                candidate = marker.group(1)
                if (candidate[0] == fence[0] and len(candidate) >= len(fence)
                        and not marker.group(2).strip()):
                    fence = None
        else:
            prose.append(line)
    if fence is not None:
        errors.append("unclosed fenced code block")

    for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", "\n".join(prose)):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        resolved = (path.parent / unquote(parsed.path)).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            errors.append(f"local link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken local link: {target}")
    return errors


def main():
    errors = []
    for name in SKILLS:
        entry = ROOT / "skills" / name / "SKILL.md"
        if not entry.is_file():
            errors.append(f"missing skill entry: {entry.relative_to(ROOT)}")
        references = entry.parent / "references"
        if not references.is_dir() or not any(references.glob("*.md")):
            errors.append(f"missing references: {name}")

    documents = [ROOT / "README.md"]
    documents += sorted((ROOT / "skills").rglob("*.md"))
    documents += sorted((ROOT / "tests").rglob("*.md"))
    for path in documents:
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative}: {error}")
            continue
        issues = check_markdown(path, text)
        if path.name == "SKILL.md":
            issues += check_metadata(path, text)
        errors.extend(f"{relative}: {issue}" for issue in issues)

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(SKILLS)} skill entries, {len(documents)} Markdown documents")
    print("Checked metadata, local link targets, fences and control characters.")
    print("LLM behavior and client compatibility require separate verification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

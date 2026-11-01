#!/usr/bin/env python3
"""Dependency-free checks for the RepoAura prompt repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = Path(".github/prompts/repo-aura.prompt.md")
README_PATH = Path("README.md")

SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        Path(entry.decode("utf-8", errors="surrogateescape"))
        for entry in result.stdout.split(b"\0")
        if entry
    ]


def remove_fenced_code(markdown: str) -> str:
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in markdown.splitlines():
        trimmed = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", trimmed)
        if marker:
            marker_text = marker.group(1)
            if fence_character is None:
                fence_character = marker_text[0]
                fence_length = len(marker_text)
            elif marker_text[0] == fence_character and len(marker_text) >= fence_length:
                fence_character = None
                fence_length = 0
            output.append("")
        elif fence_character is None:
            output.append(line)
        else:
            output.append("")
    return "\n".join(output)


def markdown_headings(markdown: str) -> set[str]:
    body = remove_fenced_code(markdown)
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", body):
        title = re.sub(r"`([^`]*)`", r"\1", match.group(1))
        slug = re.sub(r"[^\w -]", "", title.lower()).strip().replace(" ", "-")
        duplicate_number = counts.get(slug, 0)
        counts[slug] = duplicate_number + 1
        slugs.add(slug if duplicate_number == 0 else f"{slug}-{duplicate_number}")
    return slugs


def markdown_fence_errors(markdown: str, source: Path) -> list[str]:
    errors: list[str] = []
    open_fence: tuple[str, int, int] | None = None
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if not match:
            continue
        marker, remainder = match.groups()
        if open_fence is None:
            open_fence = (marker[0], len(marker), line_number)
        elif marker[0] == open_fence[0] and len(marker) >= open_fence[1] and not remainder.strip():
            open_fence = None
    if open_fence is not None:
        errors.append(f"{source.as_posix()}:{open_fence[2]}: unclosed Markdown code fence")
    return errors


def markdown_link_errors(markdown: str, source: Path, root: Path = ROOT) -> list[str]:
    body = remove_fenced_code(markdown)
    source_name = source.as_posix()
    errors: list[str] = []

    for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", body):
        raw_target = match.group(1).strip()
        destination_match = re.match(r"<?([^\s>]+)>?", raw_target)
        if not destination_match:
            continue
        target = unquote(destination_match.group(1))
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue

        path_part, separator, fragment = target.partition("#")
        resolved: Path | None = None
        if path_part:
            resolved = (root / source.parent / path_part).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{source_name}: link escapes repository root: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{source_name}: missing local link target: {target}")
                continue
            if resolved.is_dir():
                indexes = (resolved / "README.md", resolved / "INDEX.md", resolved / "index.md")
                if not any(index.is_file() for index in indexes):
                    errors.append(f"{source_name}: directory link has no README/INDEX target: {target}")
                    continue

        if separator:
            target_headings = markdown_headings(markdown) if not path_part or path_part == source_name else set()
            if resolved is not None and resolved.is_file() and resolved.suffix.lower() == ".md":
                target_headings = markdown_headings(resolved.read_text(encoding="utf-8"))
            if fragment not in target_headings:
                errors.append(f"{source_name}: missing heading anchor: {target}")
    return errors


def lint_repository() -> list[str]:
    errors: list[str] = []
    prompt_file = ROOT / PROMPT_PATH

    files = tracked_files()
    markdown_files = sorted(
        (path for path in files if path.suffix.lower() == ".md" and not (ROOT / path).is_symlink()),
        key=lambda path: path.as_posix().lower(),
    )
    for relative_path in markdown_files:
        file_path = ROOT / relative_path
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            errors.append(f"{relative_path.as_posix()}: missing final newline")
        errors.extend(markdown_fence_errors(text, relative_path))
        errors.extend(markdown_link_errors(text, relative_path))

    for relative_path in (PROMPT_PATH, README_PATH):
        if not (ROOT / relative_path).is_file():
            errors.append(f"required file is missing: {relative_path.as_posix()}")

    prompt = ""
    if prompt_file.is_file():
        prompt = prompt_file.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", prompt, re.DOTALL)
        if not frontmatter:
            errors.append(f"{PROMPT_PATH.as_posix()}: missing YAML frontmatter")
        else:
            metadata = frontmatter.group(1)
            for key in ("name", "description", "agent"):
                if not re.search(rf"(?m)^{key}:\s*\S.*$", metadata):
                    errors.append(f"{PROMPT_PATH.as_posix()}: missing frontmatter field: {key}")
            if not re.search(r"(?m)^name:\s*repo-aura\s*$", metadata):
                errors.append(f"{PROMPT_PATH.as_posix()}: name must be repo-aura")

    readme_file = ROOT / README_PATH
    if readme_file.is_file():
        readme = readme_file.read_text(encoding="utf-8")
        version_match = re.search(r"(?m)^\*\*Version:\*\*\s*([0-9.]+)", prompt)
        if version_match and version_match.group(1) not in readme:
            errors.append(f"{README_PATH.as_posix()}: does not mention prompt version {version_match.group(1)}")

    return errors


def find_secret_matches(text: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule_name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                matches.append((line_number, rule_name))
    return matches


def secret_findings() -> list[str]:
    findings: list[str] = []
    for relative_path in tracked_files():
        file_path = ROOT / relative_path
        if file_path.is_symlink():
            continue
        try:
            file_path.resolve(strict=True).relative_to(ROOT.resolve())
        except (OSError, ValueError):
            continue
        if not file_path.is_file():
            continue
        try:
            if file_path.stat().st_size > 5_000_000:
                findings.append(f"{relative_path.as_posix()}: exceeds 5 MB scan limit")
                continue
            content = file_path.read_bytes()
        except OSError as error:
            findings.append(f"{relative_path.as_posix()}: unable to read ({error.__class__.__name__})")
            continue
        if b"\0" in content:
            continue
        text = content.decode("utf-8", errors="replace")
        for line_number, rule_name in find_secret_matches(text):
            findings.append(f"{relative_path.as_posix()}:{line_number}: potential {rule_name}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--lint", action="store_true", help="check README links and prompt metadata")
    modes.add_argument("--security", action="store_true", help="scan tracked files for selected secret patterns")
    args = parser.parse_args(argv)

    label = "Lint" if args.lint else "Security scan"
    try:
        errors = lint_repository() if args.lint else secret_findings()
    except (OSError, subprocess.SubprocessError) as error:
        print(f"{label} could not complete ({error.__class__.__name__}).", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"::error::{label}: {error}")
        print(f"{label} failed with {len(errors)} finding(s).")
        return 1

    print(f"{label} passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.validate_repo import (
    find_secret_matches,
    markdown_fence_errors,
    markdown_headings,
    markdown_link_errors,
    remove_fenced_code,
)


class MarkdownValidationTests(unittest.TestCase):
    def test_removes_fenced_code_using_backticks_or_tildes(self):
        markdown = "Text\n\n~~~md\n[example](missing.md)\n~~~\n"
        self.assertNotIn("[example]", remove_fenced_code(markdown))

    def test_creates_github_style_duplicate_heading_anchors(self):
        self.assertEqual(markdown_headings("## Setup\n## Setup\n"), {"setup", "setup-1"})

    def test_detects_unclosed_markdown_fence(self):
        errors = markdown_fence_errors("```python\nprint('hello')\n", Path("README.md"))
        self.assertEqual(len(errors), 1)
        self.assertIn("unclosed Markdown code fence", errors[0])

    def test_detects_missing_local_link(self):
        with TemporaryDirectory() as temporary_directory:
            errors = markdown_link_errors(
                "[missing](not-here.md)\n",
                Path("README.md"),
                Path(temporary_directory),
            )
        self.assertEqual(len(errors), 1)
        self.assertIn("missing local link target", errors[0])

    def test_accepts_existing_cross_file_anchor(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "guide.md").write_text("# Details\n", encoding="utf-8")
            errors = markdown_link_errors("[guide](guide.md#details)\n", Path("README.md"), root)
        self.assertEqual(errors, [])

    def test_rejects_cross_file_missing_anchor(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "guide.md").write_text("# Details\n", encoding="utf-8")
            errors = markdown_link_errors("[guide](guide.md#missing)\n", Path("README.md"), root)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing heading anchor", errors[0])

    def test_rejects_link_outside_repository_root(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            errors = markdown_link_errors("[outside](../outside.md)\n", Path("README.md"), root)
        self.assertEqual(len(errors), 1)
        self.assertIn("escapes repository root", errors[0])

    def test_secret_scanner_returns_rule_and_line_not_secret_value(self):
        test_credential = "AKIA" + "1234567890ABCDEF"
        findings = find_secret_matches(f"credential={test_credential}\n")
        self.assertEqual(findings, [(1, "aws-access-key")])
        self.assertNotIn(test_credential, str(findings))


if __name__ == "__main__":
    unittest.main()

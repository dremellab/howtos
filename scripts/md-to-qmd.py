#!/usr/bin/env python3
"""Convert markdown content to QMD while preserving frontmatter."""

import sys
import re
from datetime import date
from pathlib import Path


def convert_md_to_qmd(md_path: str, qmd_path: str) -> None:
    """Update QMD file with content from MD file, preserving QMD frontmatter."""
    md_file = Path(md_path)
    qmd_file = Path(qmd_path)

    # Read markdown file (skip any frontmatter)
    md_content = md_file.read_text()
    md_body = re.sub(r"^---\n.*?\n---\n", "", md_content, flags=re.DOTALL).strip()

    # Read existing QMD to preserve frontmatter
    qmd_content = qmd_file.read_text()

    # Extract frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", qmd_content, re.DOTALL)
    if not fm_match:
        print(f"Warning: Could not find frontmatter in {qmd_path}", file=sys.stderr)
        return

    frontmatter = fm_match.group(1)

    # Update date in frontmatter
    today = date.today().strftime("%B %d, %Y")
    frontmatter = re.sub(r"date: [^\n]+", f"date: {today}", frontmatter)

    # Update date in include-before-body HTML
    frontmatter = re.sub(
        r"(<span class=\"date-value\">)[^<]+(</span>\s+</div>\s+<div>)",
        rf"\1{today}\2",
        frontmatter,
    )

    # Write updated QMD with preserved frontmatter and updated body
    qmd_file.write_text(f"---\n{frontmatter}\n---\n\n{md_body}\n")
    print(f"Updated {qmd_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: md-to-qmd.py <md_file> <qmd_file>", file=sys.stderr)
        sys.exit(1)

    convert_md_to_qmd(sys.argv[1], sys.argv[2])

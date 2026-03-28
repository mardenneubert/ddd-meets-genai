#!/usr/bin/env python3
"""Validate Mermaid syntax in a generated diagrams Markdown file.

Extracts each fenced ```mermaid block, determines its diagram type
(classDiagram, flowchart, stateDiagram-v2), and checks for constructs
that are invalid in that diagram type.

This is NOT a full Mermaid parser — it is a targeted linter that catches
the most common mistakes when generating diagrams from DMML, especially
flowchart syntax leaking into class diagrams.

Usage:
    python validate_mermaid_syntax.py <diagrams.md>

Exit codes:
    0 — no issues found
    1 — one or more issues found
    2 — usage error
"""

import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MermaidBlock:
    """A single fenced mermaid code block extracted from the Markdown."""
    file_line_start: int          # 1-based line in the .md file
    diagram_type: Optional[str] = None  # 'classDiagram', 'flowchart', 'stateDiagram-v2', etc.
    lines: List[str] = field(default_factory=list)  # raw lines (no fence markers)


@dataclass
class Issue:
    """A syntax issue found in a diagram block."""
    file_line: int    # 1-based line in the .md file
    block_line: int   # 1-based line within the mermaid block
    diagram_type: str
    rule: str         # short rule identifier
    message: str      # human-readable explanation
    line_text: str    # the offending line


# ---------------------------------------------------------------------------
# Block extraction
# ---------------------------------------------------------------------------

def extract_blocks(lines: List[str]) -> List[MermaidBlock]:
    """Extract all ```mermaid ... ``` blocks from the Markdown lines."""
    blocks: List[MermaidBlock] = []
    current: Optional[MermaidBlock] = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "```mermaid":
            current = MermaidBlock(file_line_start=i + 1)
            continue
        if current is not None and stripped == "```":
            # Determine diagram type from the first non-blank, non-frontmatter line
            in_frontmatter = False
            for bl in current.lines:
                s = bl.strip()
                if s == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter or s == "" or s.startswith("%%"):
                    continue
                if s.startswith("classDiagram"):
                    current.diagram_type = "classDiagram"
                elif s.startswith("flowchart"):
                    current.diagram_type = "flowchart"
                elif s.startswith("stateDiagram"):
                    current.diagram_type = "stateDiagram-v2"
                break
            blocks.append(current)
            current = None
            continue
        if current is not None:
            current.lines.append(line)

    return blocks


# ---------------------------------------------------------------------------
# Rules — class diagram
# ---------------------------------------------------------------------------

# Patterns that are INVALID inside classDiagram blocks
CLASS_DIAGRAM_RULES = [
    # -.-> is flowchart dotted arrow; classDiagram uses ..>
    (
        re.compile(r"-\.->"),
        "no-flowchart-dotted-arrow",
        '`-.->` is flowchart-only; use `..>` for dashed arrows in class diagrams',
    ),
    # ["label"] square-bracket node alias — flowchart only
    (
        re.compile(r'\w\["[^"]*"\]'),
        "no-square-bracket-alias",
        '`["label"]` node aliases are flowchart-only; declare a `class` instead',
    ),
    # -->|label| pipe-delimited edge labels — flowchart only
    (
        re.compile(r"-->\|"),
        "no-pipe-edge-label",
        '`-->|label|` is flowchart-only; use `: label` suffix in class diagrams',
    ),
    # subgraph ... end — flowchart only
    (
        re.compile(r"^\s*subgraph\b"),
        "no-subgraph",
        '`subgraph` is flowchart-only; use `%%` comments for grouping in class diagrams',
    ),
    # direction LR/TB — flowchart only
    (
        re.compile(r"^\s*direction\s+(LR|RL|TB|BT)\b"),
        "no-direction",
        '`direction` is flowchart-only; not valid in class diagrams',
    ),
    # ::: inline style — Mermaid 10.x only, breaks 9.x
    (
        re.compile(r":::\w"),
        "no-triple-colon",
        '`:::` inline style syntax is Mermaid 10.x only; use `cssClass "X" name` instead',
    ),
    # namespace blocks — buggy in all versions
    (
        re.compile(r"^\s*namespace\b"),
        "no-namespace",
        '`namespace` blocks silently drop relationships; use `%%` comments instead',
    ),
]

# Detect `class X cssName` misuse (style assignment that only works in flowcharts).
# Must distinguish from legitimate class declarations like `class Foo {` or
# `class Foo` (bare declaration).
CLASS_STYLE_PATTERN = re.compile(
    r"^\s*class\s+(\S+)\s+(aggregateRoot|entity|valueObject|command|domainEvent|"
    r"policy|readModel|domainService|repository|factory|specification)\s*$"
)


def check_class_diagram(block: MermaidBlock) -> List[Issue]:
    """Check a classDiagram block for invalid constructs."""
    issues: List[Issue] = []
    for j, line in enumerate(block.lines):
        file_line = block.file_line_start + j + 1
        block_line = j + 1
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("%%"):
            continue
        # Skip classDef lines (they legitimately contain style text)
        if stripped.startswith("classDef "):
            continue

        # Check regex-based rules
        for pattern, rule_id, message in CLASS_DIAGRAM_RULES:
            if pattern.search(stripped):
                issues.append(Issue(
                    file_line=file_line,
                    block_line=block_line,
                    diagram_type="classDiagram",
                    rule=rule_id,
                    message=message,
                    line_text=stripped,
                ))

        # Check class-as-style misuse
        m = CLASS_STYLE_PATTERN.match(stripped)
        if m:
            class_name, css_name = m.group(1), m.group(2)
            issues.append(Issue(
                file_line=file_line,
                block_line=block_line,
                diagram_type="classDiagram",
                rule="no-class-style-assignment",
                message=(
                    f'`class {class_name} {css_name}` declares a new class '
                    f'named "{class_name}{css_name}"; '
                    f'use `cssClass "{class_name}" {css_name}` to apply a style'
                ),
                line_text=stripped,
            ))

    return issues


# ---------------------------------------------------------------------------
# Rules — state diagram
# ---------------------------------------------------------------------------

def check_state_diagram(block: MermaidBlock) -> List[Issue]:
    """Check a stateDiagram-v2 block for common issues."""
    issues: List[Issue] = []
    for j, line in enumerate(block.lines):
        file_line = block.file_line_start + j + 1
        block_line = j + 1
        stripped = line.strip()

        if stripped.startswith("%%"):
            continue

        # ::: is also invalid in state diagrams on Mermaid 9.x
        if re.search(r":::\w", stripped):
            issues.append(Issue(
                file_line=file_line,
                block_line=block_line,
                diagram_type="stateDiagram-v2",
                rule="no-triple-colon",
                message='`:::` inline style syntax is Mermaid 10.x only',
                line_text=stripped,
            ))

    return issues


# ---------------------------------------------------------------------------
# Rules — flowchart (lighter checks, mostly version compatibility)
# ---------------------------------------------------------------------------

def check_flowchart(block: MermaidBlock) -> List[Issue]:
    """Check a flowchart block for version-compatibility issues."""
    issues: List[Issue] = []
    for j, line in enumerate(block.lines):
        file_line = block.file_line_start + j + 1
        block_line = j + 1
        stripped = line.strip()

        if stripped.startswith("%%"):
            continue

        if re.search(r":::\w", stripped):
            issues.append(Issue(
                file_line=file_line,
                block_line=block_line,
                diagram_type="flowchart",
                rule="no-triple-colon",
                message='`:::` inline style syntax is Mermaid 10.x only; use `class X cssName` instead',
                line_text=stripped,
            ))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(filepath: str) -> List[Issue]:
    """Validate all mermaid blocks in a Markdown file."""
    with open(filepath) as f:
        lines = f.readlines()

    blocks = extract_blocks(lines)
    all_issues: List[Issue] = []

    for block in blocks:
        if block.diagram_type == "classDiagram":
            all_issues.extend(check_class_diagram(block))
        elif block.diagram_type == "stateDiagram-v2":
            all_issues.extend(check_state_diagram(block))
        elif block.diagram_type == "flowchart":
            all_issues.extend(check_flowchart(block))

    return all_issues


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <diagrams.md>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]
    issues = validate(filepath)

    # Extract blocks for summary
    with open(filepath) as f:
        blocks = extract_blocks(f.readlines())

    block_summary = {}
    for b in blocks:
        t = b.diagram_type or "unknown"
        block_summary[t] = block_summary.get(t, 0) + 1

    print("=" * 60)
    print(f"Mermaid Syntax Check: {filepath.split('/')[-1]}")
    print("=" * 60)
    print(f"  Diagram blocks found: {len(blocks)}")
    for dtype, count in sorted(block_summary.items()):
        print(f"    {dtype}: {count}")
    print()

    if not issues:
        print("  RESULT: PASS (no syntax issues found)")
        print()
        sys.exit(0)

    # Group issues by rule
    by_rule: dict[str, list[Issue]] = {}
    for issue in issues:
        by_rule.setdefault(issue.rule, []).append(issue)

    print(f"  Issues found: {len(issues)}")
    print()

    for rule_id, rule_issues in sorted(by_rule.items()):
        print(f"  [{rule_id}] ({len(rule_issues)} occurrence{'s' if len(rule_issues) > 1 else ''})")
        print(f"    {rule_issues[0].message}")
        print()
        for issue in rule_issues:
            print(f"    Line {issue.file_line} (block line {issue.block_line}):")
            print(f"      {issue.line_text}")
        print()

    print(f"  RESULT: FAIL ({len(issues)} issue{'s' if len(issues) > 1 else ''} found)")
    print()
    sys.exit(1)


if __name__ == "__main__":
    main()

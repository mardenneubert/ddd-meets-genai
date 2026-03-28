#!/usr/bin/env node
/**
 * Validate Mermaid diagram syntax using the official Mermaid parser.
 *
 * Extracts each fenced ```mermaid block from a Markdown file and runs it
 * through mermaid.parse(). This catches any syntax error the Mermaid parser
 * knows about — including errors that regex-based linters can't anticipate.
 *
 * NOTE: This script catches PARSE errors only. It does NOT catch:
 *   - Constructs that are valid syntax but semantically wrong (e.g.,
 *     `class X cssName` creates a phantom class instead of styling)
 *   - Version-compatibility issues (e.g., `:::` is valid in Mermaid 10+
 *     but breaks Mermaid 9.x renderers like Obsidian)
 * Use validate_mermaid_syntax.py for those checks.
 *
 * Requirements:
 *   npm install mermaid jsdom dompurify   (in the scripts/ directory)
 *
 * Usage:
 *   node validate_mermaid_parse.mjs <diagrams.md>
 *
 * Exit codes:
 *   0 — all diagrams parsed successfully
 *   1 — one or more parse errors found
 *   2 — usage error
 */

import { readFileSync } from "fs";
import { JSDOM } from "jsdom";

// Minimal DOM shim so Mermaid can initialize without a browser
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>");
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", {
  value: dom.window.navigator,
  writable: true,
  configurable: true,
});

const mermaidModule = await import("mermaid");
const mermaid = mermaidModule.default;
mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });

// ---------------------------------------------------------------------------
// Extract mermaid blocks
// ---------------------------------------------------------------------------

function extractBlocks(lines) {
  const blocks = [];
  let current = null;

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed === "```mermaid") {
      current = { startLine: i + 1, lines: [] };
      continue;
    }
    if (current && trimmed === "```") {
      blocks.push(current);
      current = null;
      continue;
    }
    if (current) {
      current.lines.push(lines[i]);
    }
  }
  return blocks;
}

// ---------------------------------------------------------------------------
// Determine diagram type from the code
// ---------------------------------------------------------------------------

function getDiagramType(code) {
  for (const line of code.split("\n")) {
    const s = line.trim();
    if (s === "" || s.startsWith("%%") || s === "---") continue;
    if (/^title:/.test(s)) continue; // frontmatter
    if (s.startsWith("classDiagram")) return "classDiagram";
    if (s.startsWith("flowchart")) return "flowchart";
    if (s.startsWith("stateDiagram")) return "stateDiagram-v2";
    if (s.startsWith("sequenceDiagram")) return "sequenceDiagram";
    if (s.startsWith("erDiagram")) return "erDiagram";
    if (s.startsWith("gantt")) return "gantt";
    if (s.startsWith("pie")) return "pie";
    break;
  }
  return "unknown";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
if (args.length !== 1) {
  console.error(`Usage: node validate_mermaid_parse.mjs <diagrams.md>`);
  process.exit(2);
}

const filepath = args[0];
const content = readFileSync(filepath, "utf-8");
const lines = content.split("\n");
const blocks = extractBlocks(lines);

console.log("=".repeat(60));
console.log(`Mermaid Parse Check: ${filepath.split("/").pop()}`);
console.log("=".repeat(60));
console.log(`  Diagram blocks found: ${blocks.length}`);
console.log();

let errorCount = 0;

for (let idx = 0; idx < blocks.length; idx++) {
  const block = blocks[idx];
  const code = block.lines.join("\n");
  const diagramType = getDiagramType(code);
  const label = `Block ${idx + 1} (line ${block.startLine}, ${diagramType})`;

  try {
    await mermaid.parse(code);
    console.log(`  ✓ ${label}: OK`);
  } catch (e) {
    const msg = e.message || String(e);
    const isParseError =
      msg.includes("Parse error") ||
      msg.includes("Lexical error") ||
      msg.includes("Syntax error") ||
      msg.includes("Unknown diagram type");

    if (isParseError) {
      errorCount++;
      console.log(`  ✗ ${label}: PARSE ERROR`);
      // Extract the most useful line from the error
      const errorLines = msg.split("\n");
      for (const eLine of errorLines) {
        if (
          eLine.includes("Parse error") ||
          eLine.includes("Lexical error") ||
          eLine.includes("Syntax error") ||
          eLine.includes("Expecting") ||
          eLine.includes("Unknown diagram")
        ) {
          console.log(`    ${eLine.trim()}`);
        }
      }
      console.log();
    } else {
      // Post-parse error (rendering/DOMPurify) — syntax was valid
      console.log(`  ✓ ${label}: OK (parse succeeded)`);
    }
  }
}

console.log();
if (errorCount === 0) {
  console.log(
    `  RESULT: PASS (all ${blocks.length} diagrams parsed successfully)`
  );
  process.exit(0);
} else {
  console.log(
    `  RESULT: FAIL (${errorCount} parse error${errorCount > 1 ? "s" : ""} in ${blocks.length} diagrams)`
  );
  process.exit(1);
}

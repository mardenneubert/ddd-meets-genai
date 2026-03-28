#!/usr/bin/env python3
"""
Validate Mermaid diagram coverage against a DMML source file.

Checks that every significant DMML element (by id or name) appears somewhere
in the output Markdown file — either as a rendered diagram element or as a
%% comment.

Usage:
    python validate_mermaid_coverage.py <dmml-file> <mermaid-md-file>

Exit codes:
    0 = all elements covered
    1 = missing elements found
    2 = usage error
"""

import re
import sys

import yaml


def extract_dmml_elements(dmml: dict) -> dict:
    """Extract all named/identified elements from a DMML structure."""
    elements = {
        "subdomains": [],
        "bounded_contexts": [],
        "context_map_relationships": [],
        "aggregates": [],
        "entities": [],
        "value_objects": [],
        "commands": [],
        "domain_events": [],
        "policies": [],
        "read_models": [],
        "domain_services": [],
        "application_services": [],
        "repositories": [],
        "factories": [],
        "specifications": [],
        "process_managers": [],
    }

    # Subdomains
    for sd in dmml.get("subdomains", []):
        elements["subdomains"].append(sd.get("name", sd.get("id", "")))

    # Bounded contexts and their contents
    for bc in dmml.get("bounded_contexts", []):
        bc_name = bc.get("name", bc.get("id", ""))
        elements["bounded_contexts"].append(bc_name)

        # Aggregates
        for agg in bc.get("aggregates", []):
            agg_name = agg.get("name", agg.get("id", ""))
            elements["aggregates"].append(agg_name)

            # Root entity
            root = agg.get("root_entity")
            if root:
                elements["entities"].append(root.get("name", root.get("id", "")))

            # Child entities
            for ent in agg.get("entities", []):
                elements["entities"].append(ent.get("name", ent.get("id", "")))

            # Value objects
            for vo in agg.get("value_objects", []):
                elements["value_objects"].append(vo.get("name", vo.get("id", "")))

            # Commands
            for cmd in agg.get("commands", []):
                elements["commands"].append(cmd.get("name", cmd.get("id", "")))

            # Domain events
            for evt in agg.get("domain_events", []):
                elements["domain_events"].append(evt.get("name", evt.get("id", "")))

            # Repository
            repo = agg.get("repository")
            if repo:
                elements["repositories"].append(repo.get("name", repo.get("id", "")))

            # Factory
            fac = agg.get("factory")
            if fac:
                elements["factories"].append(fac.get("name", fac.get("id", "")))

            # Specifications
            for spec in agg.get("specifications", []):
                elements["specifications"].append(spec.get("name", spec.get("id", "")))

        # Policies
        for pol in bc.get("policies", []):
            elements["policies"].append(pol.get("name", pol.get("id", "")))

        # Read models
        for rm in bc.get("read_models", []):
            elements["read_models"].append(rm.get("name", rm.get("id", "")))

        # Domain services
        for svc in bc.get("domain_services", []):
            elements["domain_services"].append(svc.get("name", svc.get("id", "")))

        # Application services
        for app in bc.get("application_services", []):
            elements["application_services"].append(app.get("name", app.get("id", "")))

        # Process managers
        for pm in bc.get("process_managers", []):
            elements["process_managers"].append(pm.get("name", pm.get("id", "")))

    # Context map relationships
    ctx_map = dmml.get("context_map", {})
    for rel in ctx_map.get("relationships", []):
        rel_name = rel.get("name", rel.get("id", ""))
        elements["context_map_relationships"].append(rel_name)

    return elements


def normalize(text: str) -> str:
    """Normalize a name for fuzzy matching: lowercase, strip spaces/hyphens."""
    return re.sub(r"[\s\-_]+", "", text.lower())


def check_coverage(elements: dict, output_text: str) -> tuple:
    """Check which DMML elements appear in the output text."""
    output_normalized = normalize(output_text)
    # Also check against the raw text for exact-ish matches
    output_lower = output_text.lower()

    missing = {}
    found_count = 0
    total_count = 0

    for category, names in elements.items():
        category_missing = []
        for name in names:
            total_count += 1
            # Try multiple matching strategies
            name_normalized = normalize(name)
            name_lower = name.lower()

            # Strategy 1: normalized substring
            if name_normalized in output_normalized:
                found_count += 1
                continue

            # Strategy 2: original name (lowercase) substring
            if name_lower in output_lower:
                found_count += 1
                continue

            # Strategy 3: PascalCase version (e.g., "Route Specification" -> "routespecification")
            pascal = name.replace(" ", "")
            if pascal.lower() in output_lower:
                found_count += 1
                continue

            # Strategy 4: kebab-case version (e.g., "Route Specification" -> "route-specification")
            kebab = name.lower().replace(" ", "-")
            if kebab in output_lower:
                found_count += 1
                continue

            category_missing.append(name)

        if category_missing:
            missing[category] = category_missing

    return found_count, total_count, missing


def main():
    if len(sys.argv) != 3:
        print("Usage: python validate_mermaid_coverage.py <dmml-file> <mermaid-md-file>")
        sys.exit(2)

    dmml_path = sys.argv[1]
    output_path = sys.argv[2]

    # Load DMML
    try:
        with open(dmml_path, "r") as f:
            dmml = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading DMML file: {e}")
        sys.exit(2)

    # Load output
    try:
        with open(output_path, "r") as f:
            output_text = f.read()
    except Exception as e:
        print(f"Error reading output file: {e}")
        sys.exit(2)

    # Extract and check
    elements = extract_dmml_elements(dmml)
    found, total, missing = check_coverage(elements, output_text)

    # Report
    header = f"Mermaid Coverage: {sys.argv[2].split('/')[-1]}"
    print("=" * 60)
    print(header)
    print("=" * 60)

    # Count diagrams
    diagram_count = output_text.count("```mermaid")
    print(f"  Mermaid diagrams found:  {diagram_count}")
    print(f"  DMML elements total:     {total}")
    print(f"  Elements covered:        {found}")
    print(f"  Elements missing:        {total - found}")
    print(f"  Coverage:                {found/total*100:.1f}%" if total > 0 else "  Coverage: N/A")
    print()

    # Per-category summary
    for category, names in elements.items():
        if not names:
            continue
        cat_missing = missing.get(category, [])
        status = "✓" if not cat_missing else f"✗ ({len(cat_missing)} missing)"
        display_cat = category.replace("_", " ").title()
        print(f"  {display_cat}: {len(names) - len(cat_missing)}/{len(names)} {status}")

    if missing:
        print()
        print("  MISSING ELEMENTS:")
        for category, names in missing.items():
            display_cat = category.replace("_", " ").title()
            for name in names:
                print(f"    [{display_cat}] {name}")
        print()
        print(f"  RESULT: INCOMPLETE ({total - found} elements missing)")
        sys.exit(1)
    else:
        print()
        print("  RESULT: COMPLETE (all elements covered)")
        sys.exit(0)


if __name__ == "__main__":
    main()

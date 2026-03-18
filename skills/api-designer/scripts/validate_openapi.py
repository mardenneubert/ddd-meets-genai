#!/usr/bin/env python3
"""
OpenAPI Validator — validates an OpenAPI 3.1 YAML file for structural
correctness and DDD API conventions.

Usage:
    python validate_openapi.py <file.openapi.yaml>

Exit codes:
    0 — valid (may have warnings)
    1 — invalid (errors found)
    2 — usage error

This is a lightweight structural validator. It does NOT perform full OpenAPI
schema validation (use a dedicated tool like swagger-cli or openapi-generator
for that). Instead, it checks the conventions specific to DDD API design as
defined by the api-designer skill.
"""

import sys
import yaml
from pathlib import Path


def validate_openapi(file_path: str) -> tuple[list[str], list[str]]:
    """Validate an OpenAPI YAML file. Returns (errors, warnings)."""
    errors = []
    warnings = []

    # --- Load and parse YAML ---
    path = Path(file_path)
    if not path.exists():
        return [f"File not found: {file_path}"], []

    try:
        with open(path, "r") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"], []

    if not isinstance(doc, dict):
        return ["Document root must be a YAML mapping"], []

    # --- Check OpenAPI version ---
    openapi_version = doc.get("openapi")
    if not openapi_version:
        errors.append("Missing 'openapi' version field")
    elif not str(openapi_version).startswith("3.1"):
        warnings.append(f"Expected OpenAPI 3.1.x, got {openapi_version}")

    # --- Check info section ---
    info = doc.get("info")
    if not info:
        errors.append("Missing 'info' section")
    else:
        if not info.get("title"):
            errors.append("Missing info.title")
        if not info.get("version"):
            errors.append("Missing info.version")
        if not info.get("description"):
            warnings.append("Missing info.description (recommended for DDD APIs)")

    # --- Check tags ---
    tags = doc.get("tags", [])
    if not tags:
        warnings.append("No tags defined (each bounded context should be a tag)")
    tag_names = {t.get("name") for t in tags if isinstance(t, dict)}

    # --- Check paths ---
    paths = doc.get("paths")
    if not paths:
        errors.append("Missing 'paths' section (no endpoints defined)")
        return errors, warnings

    post_count = 0
    get_count = 0
    other_count = 0
    operations_without_tags = []
    operations_without_operationid = []
    all_operation_ids = []

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            errors.append(f"Path '{path_str}' is not a valid mapping")
            continue

        # Check path naming convention (kebab-case)
        segments = path_str.strip("/").split("/")
        for seg in segments:
            if seg.startswith("{"):
                continue  # path parameter
            if seg != seg.lower():
                warnings.append(
                    f"Path segment '{seg}' in '{path_str}' is not lowercase"
                )

        for method in ["get", "post", "put", "patch", "delete"]:
            operation = path_item.get(method)
            if not operation:
                continue

            if method == "post":
                post_count += 1
            elif method == "get":
                get_count += 1
            else:
                other_count += 1

            # Check operation has tags
            op_tags = operation.get("tags", [])
            if not op_tags:
                operations_without_tags.append(f"{method.upper()} {path_str}")
            else:
                for t in op_tags:
                    if t not in tag_names:
                        warnings.append(
                            f"Tag '{t}' on {method.upper()} {path_str} "
                            f"not defined in top-level tags"
                        )

            # Check operationId
            op_id = operation.get("operationId")
            if not op_id:
                operations_without_operationid.append(
                    f"{method.upper()} {path_str}"
                )
            else:
                all_operation_ids.append(op_id)

            # Check responses
            responses = operation.get("responses")
            if not responses:
                errors.append(
                    f"{method.upper()} {path_str}: missing responses section"
                )

            # Check POST operations have requestBody (except when no body needed)
            if method == "post" and not operation.get("requestBody"):
                # Some POST commands (like pack-order) may not need a body
                warnings.append(
                    f"POST {path_str}: no requestBody defined "
                    f"(acceptable for bodyless commands)"
                )

            # Check for summary
            if not operation.get("summary"):
                warnings.append(
                    f"{method.upper()} {path_str}: missing summary"
                )

    if operations_without_tags:
        for op in operations_without_tags:
            warnings.append(f"{op}: no tags (should reference a bounded context)")

    if operations_without_operationid:
        for op in operations_without_operationid:
            errors.append(f"{op}: missing operationId")

    # Check for duplicate operationIds
    seen_ids = set()
    for oid in all_operation_ids:
        if oid in seen_ids:
            errors.append(f"Duplicate operationId: {oid}")
        seen_ids.add(oid)

    # DDD convention: expect POST (commands) and GET (queries)
    if post_count == 0:
        warnings.append("No POST endpoints (expected command endpoints)")
    if get_count == 0:
        warnings.append("No GET endpoints (expected query endpoints)")
    if other_count > 0:
        warnings.append(
            f"Found {other_count} non-GET/POST operations "
            f"(DDD APIs typically use POST for commands and GET for queries)"
        )

    # --- Check components/schemas ---
    components = doc.get("components", {})
    schemas = components.get("schemas", {})

    if not schemas:
        warnings.append("No schemas defined in components/schemas")

    # Check for ErrorResponse schema
    if "ErrorResponse" not in schemas:
        warnings.append(
            "Missing 'ErrorResponse' schema (standard error format expected)"
        )

    # Check all $ref references resolve
    unresolved_refs = []
    _check_refs(doc, schemas, unresolved_refs, "#/components/schemas/")
    for ref in unresolved_refs:
        errors.append(f"Unresolved $ref: {ref}")

    # Check schema naming convention (PascalCase)
    for schema_name in schemas:
        if schema_name[0].islower():
            warnings.append(
                f"Schema '{schema_name}' starts with lowercase "
                f"(PascalCase expected)"
            )

    # --- Summary stats ---
    print(f"\n{'='*60}")
    print(f"OpenAPI Validation: {path.name}")
    print(f"{'='*60}")
    print(f"  OpenAPI version:  {openapi_version}")
    print(f"  Tags:             {len(tags)}")
    print(f"  POST endpoints:   {post_count} (commands)")
    print(f"  GET endpoints:    {get_count} (queries)")
    print(f"  Other endpoints:  {other_count}")
    print(f"  Schemas:          {len(schemas)}")
    print(f"  Operation IDs:    {len(all_operation_ids)}")

    return errors, warnings


def _check_refs(
    node: any,
    schemas: dict,
    unresolved: list,
    prefix: str,
):
    """Recursively check all $ref values resolve to defined schemas."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref and isinstance(ref, str) and ref.startswith(prefix):
            schema_name = ref[len(prefix) :]
            if schema_name not in schemas:
                if ref not in unresolved:
                    unresolved.append(ref)
        for value in node.values():
            _check_refs(value, schemas, unresolved, prefix)
    elif isinstance(node, list):
        for item in node:
            _check_refs(item, schemas, unresolved, prefix)


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_openapi.py <file.openapi.yaml>")
        sys.exit(2)

    file_path = sys.argv[1]
    errors, warnings = validate_openapi(file_path)

    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"    ⚠  {w}")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors:
            print(f"    ✗  {e}")
        print(f"\n  RESULT: INVALID ({len(errors)} errors, {len(warnings)} warnings)")
        sys.exit(1)
    else:
        print(f"\n  RESULT: VALID ({len(warnings)} warnings)")
        sys.exit(0)


if __name__ == "__main__":
    main()

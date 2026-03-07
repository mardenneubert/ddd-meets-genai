#!/usr/bin/env python3
"""
DMML Validator — validates a DMML YAML file against the DMML specification.

Usage:
    python validate_dmml.py <file.dmml.yaml>

Exit codes:
    0 — valid (may have warnings)
    1 — invalid (errors found)
    2 — usage error
"""

import sys
import yaml
from pathlib import Path
from collections import Counter

# --- Constants ---

VALID_STATUSES = {"draft", "proposed", "accepted"}

VALID_RELATIONSHIP_TYPES = {
    "partnership", "shared_kernel", "customer_supplier", "conformist",
    "anticorruption_layer", "open_host_service", "published_language",
    "separate_ways", "big_ball_of_mud",
}

SYMMETRIC_RELATIONSHIP_TYPES = {
    "partnership", "shared_kernel", "published_language", "separate_ways",
}

ID_PREFIX_MAP = {
    "sd-": "subdomain",
    "bc-": "bounded_context",
    "agg-": "aggregate",
    "ent-": "entity",
    "vo-": "value_object",
    "evt-": "domain_event",
    "cmd-": "command",
    "svc-": "domain_service",
    "app-": "application_service",
    "pol-": "policy",
    "pm-": "process_manager",
    "repo-": "repository",
    "repo_": "repository",  # tolerate underscore
    "fac-": "factory",
    "spec-": "specification",
    "rm-": "read_model",
    "mod-": "module",
    "rel-": "context_map_relationship",
    "term-": "ubiquitous_language_term",
}

ELEMENT_TYPE_TO_PREFIX = {
    "subdomain": "sd-",
    "bounded_context": "bc-",
    "aggregate": "agg-",
    "entity": "ent-",
    "value_object": "vo-",
    "domain_event": "evt-",
    "command": "cmd-",
    "domain_service": "svc-",
    "application_service": "app-",
    "policy": "pol-",
    "process_manager": "pm-",
    "repository": "repo-",
    "factory": "fac-",
    "specification": "spec-",
    "read_model": "rm-",
    "module": "mod-",
    "context_map_relationship": "rel-",
    "ubiquitous_language_term": "term-",
}


class DmmlValidator:
    def __init__(self, doc):
        self.doc = doc
        self.errors = []
        self.warnings = []
        self.all_ids = {}  # id -> element_type

    def error(self, msg):
        self.errors.append(f"ERROR: {msg}")

    def warn(self, msg):
        self.warnings.append(f"WARNING: {msg}")

    def validate(self):
        if not isinstance(self.doc, dict):
            self.error("Document root must be a YAML mapping")
            return

        self._check_envelope()
        self._collect_all_ids()
        self._check_id_uniqueness()
        self._check_id_prefixes()
        self._check_subdomains()
        self._check_bounded_contexts()
        self._check_context_map()
        self._check_cross_references()

    # --- Envelope ---

    def _check_envelope(self):
        if "dmml" not in self.doc:
            self.error("Missing required 'dmml' version field")
        if "model" not in self.doc:
            self.error("Missing required 'model' section")
        else:
            model = self.doc["model"]
            if not isinstance(model, dict):
                self.error("'model' must be a mapping")
            else:
                if "name" not in model:
                    self.error("Missing required 'model.name'")
                if "status" not in model:
                    self.error("Missing required 'model.status'")
                elif model["status"] not in VALID_STATUSES:
                    self.error(f"Invalid model.status: '{model['status']}' — must be one of {VALID_STATUSES}")

        if "subdomains" not in self.doc or not self.doc.get("subdomains"):
            self.error("At least one 'subdomains' entry is required")
        if "bounded_contexts" not in self.doc or not self.doc.get("bounded_contexts"):
            self.error("At least one 'bounded_contexts' entry is required")

    # --- ID Collection ---

    def _collect_all_ids(self):
        """Walk the entire document and collect all 'id' fields."""
        # Subdomains
        for sd in self.doc.get("subdomains") or []:
            self._register_id(sd, "subdomain")

        # Bounded contexts and their nested elements
        for bc in self.doc.get("bounded_contexts") or []:
            self._register_id(bc, "bounded_context")

            # Ubiquitous language terms
            for term in bc.get("ubiquitous_language") or []:
                self._register_id(term, "ubiquitous_language_term")

            # Aggregates and their children
            for agg in bc.get("aggregates") or []:
                self._register_id(agg, "aggregate")

                # Root entity
                root = agg.get("root_entity")
                if root:
                    self._register_id(root, "entity")

                # Child entities
                for ent in agg.get("entities") or []:
                    self._register_id(ent, "entity")

                # Value objects
                for vo in agg.get("value_objects") or []:
                    self._register_id(vo, "value_object")

                # Domain events
                for evt in agg.get("domain_events") or []:
                    self._register_id(evt, "domain_event")

                # Commands
                for cmd in agg.get("commands") or []:
                    self._register_id(cmd, "command")

                # Repository
                repo = agg.get("repository")
                if repo:
                    self._register_id(repo, "repository")

                # Factory
                fac = agg.get("factory")
                if fac:
                    self._register_id(fac, "factory")

                # Specifications
                for spec in agg.get("specifications") or []:
                    self._register_id(spec, "specification")

            # Domain services
            for svc in bc.get("domain_services") or []:
                self._register_id(svc, "domain_service")

            # Application services
            for app in bc.get("application_services") or []:
                self._register_id(app, "application_service")

            # Policies
            for pol in bc.get("policies") or []:
                self._register_id(pol, "policy")

            # Process managers
            for pm in bc.get("process_managers") or []:
                self._register_id(pm, "process_manager")

            # Read models
            for rm in bc.get("read_models") or []:
                self._register_id(rm, "read_model")

            # Modules
            for mod in bc.get("modules") or []:
                self._register_id(mod, "module")

        # Context map relationships
        cm = self.doc.get("context_map")
        if cm and isinstance(cm, dict):
            for rel in cm.get("relationships") or []:
                self._register_id(rel, "context_map_relationship")

    def _register_id(self, element, element_type):
        if not isinstance(element, dict):
            return
        eid = element.get("id")
        if eid:
            if eid in self.all_ids:
                self.error(f"Duplicate ID: '{eid}' (already registered as {self.all_ids[eid]})")
            else:
                self.all_ids[eid] = element_type

            # Validate status if present
            status = element.get("status")
            if status and status not in VALID_STATUSES:
                self.error(f"Invalid status '{status}' on element '{eid}' — must be one of {VALID_STATUSES}")

    # --- ID Uniqueness ---

    def _check_id_uniqueness(self):
        # Already handled in _register_id
        pass

    # --- ID Prefixes ---

    def _check_id_prefixes(self):
        for eid, etype in self.all_ids.items():
            expected_prefix = ELEMENT_TYPE_TO_PREFIX.get(etype)
            if expected_prefix and not eid.startswith(expected_prefix):
                self.error(f"ID '{eid}' (type: {etype}) should start with '{expected_prefix}'")

    # --- Subdomains ---

    def _check_subdomains(self):
        for sd in self.doc.get("subdomains") or []:
            if not isinstance(sd, dict):
                continue
            if "id" not in sd:
                self.error("Subdomain missing required 'id' field")
            if "classification" not in sd:
                self.error(f"Subdomain '{sd.get('id', '?')}' missing required 'classification'")
            elif sd["classification"] not in {"core", "supporting", "generic"}:
                self.error(f"Subdomain '{sd.get('id')}' has invalid classification: '{sd['classification']}'")

    # --- Bounded Contexts ---

    def _check_bounded_contexts(self):
        subdomain_ids = {sd.get("id") for sd in (self.doc.get("subdomains") or []) if isinstance(sd, dict)}

        for bc in self.doc.get("bounded_contexts") or []:
            if not isinstance(bc, dict):
                continue
            bc_id = bc.get("id", "?")

            # Required: subdomain reference
            sd_ref = bc.get("subdomain")
            if not sd_ref:
                self.error(f"Bounded context '{bc_id}' missing required 'subdomain' reference")
            elif sd_ref not in subdomain_ids:
                self.error(f"Bounded context '{bc_id}' references non-existent subdomain '{sd_ref}'")

            # Required: responsibilities
            if not bc.get("responsibilities"):
                self.error(f"Bounded context '{bc_id}' missing required 'responsibilities'")

            # Check aggregates
            aggregates = bc.get("aggregates") or []
            if not aggregates:
                self.warn(f"Bounded context '{bc_id}' has no aggregates (strategic-only model)")

            for agg in aggregates:
                self._check_aggregate(agg, bc_id)

            # Warnings for empty tactical sections
            for pol in bc.get("policies") or []:
                if isinstance(pol, dict):
                    if not pol.get("trigger_events"):
                        self.warn(f"Policy '{pol.get('id', '?')}' has no trigger_events")
                    if not pol.get("issues_commands"):
                        self.warn(f"Policy '{pol.get('id', '?')}' has no issues_commands")

    def _check_aggregate(self, agg, bc_id):
        if not isinstance(agg, dict):
            return
        agg_id = agg.get("id", "?")

        # Required: root_entity
        root = agg.get("root_entity")
        if not root:
            self.error(f"Aggregate '{agg_id}' in '{bc_id}' missing required 'root_entity'")
        elif isinstance(root, dict):
            if not root.get("identity"):
                self.error(f"Root entity '{root.get('id', '?')}' in aggregate '{agg_id}' missing 'identity'")

        # Warnings
        if not agg.get("domain_events"):
            self.warn(f"Aggregate '{agg_id}' has no domain_events")

        for cmd in agg.get("commands") or []:
            if isinstance(cmd, dict) and not cmd.get("preconditions"):
                self.warn(f"Command '{cmd.get('id', '?')}' has no preconditions")

        # Check entities have fields
        for ent in agg.get("entities") or []:
            if isinstance(ent, dict) and not ent.get("fields"):
                self.warn(f"Entity '{ent.get('id', '?')}' has no fields beyond identity")

        # Value objects need equality
        for vo in agg.get("value_objects") or []:
            if isinstance(vo, dict):
                if not vo.get("fields"):
                    self.error(f"Value object '{vo.get('id', '?')}' must have at least one field")
                if not vo.get("equality"):
                    self.error(f"Value object '{vo.get('id', '?')}' missing required 'equality' field")

        # Domain services need operations
        # (domain_services are at BC level, not aggregate, but check if nested here by mistake)

    # --- Context Map ---

    def _check_context_map(self):
        cm = self.doc.get("context_map")
        if not cm:
            return
        if not isinstance(cm, dict):
            self.error("'context_map' must be a mapping")
            return

        for rel in cm.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            rel_id = rel.get("id", "?")

            # Validate relationship type
            rel_type = rel.get("type")
            if rel_type:
                types_to_check = rel_type if isinstance(rel_type, list) else [rel_type]
                for t in types_to_check:
                    if t not in VALID_RELATIONSHIP_TYPES:
                        self.error(f"Relationship '{rel_id}' has invalid type: '{t}'")

                # Symmetric check
                for t in types_to_check:
                    if t in SYMMETRIC_RELATIONSHIP_TYPES:
                        if rel.get("upstream") or rel.get("downstream"):
                            self.warn(
                                f"Relationship '{rel_id}' has symmetric type '{t}' "
                                f"but uses upstream/downstream. Consider using 'participants' instead."
                            )
            else:
                self.error(f"Relationship '{rel_id}' missing required 'type'")

            # Validate upstream/downstream or participants references
            upstream = rel.get("upstream")
            downstream = rel.get("downstream")
            participants = rel.get("participants")

            if not participants and not (upstream and downstream):
                self.error(f"Relationship '{rel_id}' must have either upstream/downstream or participants")

    # --- Cross-References ---

    def _check_cross_references(self):
        """Check that all cross-referenced IDs exist in the document."""
        # Gather all reference fields
        refs_to_check = []

        for bc in self.doc.get("bounded_contexts") or []:
            if not isinstance(bc, dict):
                continue
            bc_id = bc.get("id", "?")

            for agg in bc.get("aggregates") or []:
                if not isinstance(agg, dict):
                    continue
                agg_id = agg.get("id", "?")

                # domain_events[].consumed_by
                for evt in agg.get("domain_events") or []:
                    if isinstance(evt, dict):
                        for ref in evt.get("consumed_by") or []:
                            refs_to_check.append((ref, f"consumed_by in {evt.get('id', '?')}"))

                # commands[].emits
                for cmd in agg.get("commands") or []:
                    if isinstance(cmd, dict):
                        for ref in cmd.get("emits") or []:
                            refs_to_check.append((ref, f"emits in {cmd.get('id', '?')}"))

            # application_services[].coordinates and handles
            for app in bc.get("application_services") or []:
                if isinstance(app, dict):
                    for ref in app.get("coordinates") or []:
                        refs_to_check.append((ref, f"coordinates in {app.get('id', '?')}"))
                    for ref in app.get("handles") or []:
                        refs_to_check.append((ref, f"handles in {app.get('id', '?')}"))

            # policies[].trigger_events and issues_commands
            for pol in bc.get("policies") or []:
                if isinstance(pol, dict):
                    for ref in pol.get("trigger_events") or []:
                        refs_to_check.append((ref, f"trigger_events in {pol.get('id', '?')}"))
                    for ref in pol.get("issues_commands") or []:
                        refs_to_check.append((ref, f"issues_commands in {pol.get('id', '?')}"))

            # process_managers[].transitions[].on_event and issues
            for pm in bc.get("process_managers") or []:
                if isinstance(pm, dict):
                    for trans in pm.get("transitions") or []:
                        if isinstance(trans, dict):
                            on_event = trans.get("on_event")
                            if on_event:
                                refs_to_check.append((on_event, f"on_event in {pm.get('id', '?')}"))
                            for ref in trans.get("issues") or []:
                                refs_to_check.append((ref, f"issues in {pm.get('id', '?')}"))

            # read_models[].subscribes_to
            for rm in bc.get("read_models") or []:
                if isinstance(rm, dict):
                    for ref in rm.get("subscribes_to") or []:
                        refs_to_check.append((ref, f"subscribes_to in {rm.get('id', '?')}"))

            # modules[].contains
            for mod in bc.get("modules") or []:
                if isinstance(mod, dict):
                    for ref in mod.get("contains") or []:
                        refs_to_check.append((ref, f"contains in {mod.get('id', '?')}"))

        # Context map upstream/downstream
        cm = self.doc.get("context_map")
        if cm and isinstance(cm, dict):
            for rel in cm.get("relationships") or []:
                if isinstance(rel, dict):
                    rel_id = rel.get("id", "?")
                    upstream = rel.get("upstream")
                    downstream = rel.get("downstream")
                    if upstream:
                        refs_to_check.append((upstream, f"upstream in {rel_id}"))
                    if downstream:
                        refs_to_check.append((downstream, f"downstream in {rel_id}"))
                    for p in rel.get("participants") or []:
                        refs_to_check.append((p, f"participants in {rel_id}"))

        # Now validate all references
        for ref_id, context in refs_to_check:
            if ref_id not in self.all_ids:
                self.error(f"Unresolved reference: '{ref_id}' (referenced in {context})")

    # --- Notes warnings ---

    def check_notes_on_drafts(self):
        """Warn about draft elements without notes."""
        for bc in self.doc.get("bounded_contexts") or []:
            if not isinstance(bc, dict):
                continue
            self._check_element_notes(bc, "bounded_context")

            for agg in bc.get("aggregates") or []:
                if isinstance(agg, dict):
                    self._check_element_notes(agg, "aggregate")

        for sd in self.doc.get("subdomains") or []:
            if isinstance(sd, dict):
                self._check_element_notes(sd, "subdomain")

    def _check_element_notes(self, element, etype):
        status = element.get("status", self.doc.get("model", {}).get("status", "draft"))
        if status == "draft" and not element.get("notes"):
            self.warn(f"{etype.replace('_', ' ').title()} '{element.get('id', '?')}' is draft but has no notes")


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_dmml.py <file.dmml.yaml>", file=sys.stderr)
        sys.exit(2)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(filepath, "r") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        sys.exit(1)

    if doc is None:
        print("ERROR: Empty document", file=sys.stderr)
        sys.exit(1)

    validator = DmmlValidator(doc)
    validator.validate()
    validator.check_notes_on_drafts()

    # --- Output ---
    if validator.errors:
        print(f"\n{'='*60}")
        print(f"VALIDATION FAILED — {len(validator.errors)} error(s)")
        print(f"{'='*60}\n")
        for e in validator.errors:
            print(f"  {e}")
    else:
        print(f"\n{'='*60}")
        print(f"VALIDATION PASSED")
        print(f"{'='*60}\n")

    if validator.warnings:
        print(f"\n{len(validator.warnings)} warning(s):\n")
        for w in validator.warnings:
            print(f"  {w}")

    # --- Summary ---
    print(f"\nSummary: {len(validator.all_ids)} elements found")
    type_counts = Counter(validator.all_ids.values())
    for etype, count in sorted(type_counts.items()):
        print(f"  {etype}: {count}")

    sys.exit(1 if validator.errors else 0)


if __name__ == "__main__":
    main()

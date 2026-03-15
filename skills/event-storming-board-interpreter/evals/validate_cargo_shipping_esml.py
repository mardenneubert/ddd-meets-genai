#!/usr/bin/env python3
"""
Validation script for Cargo Shipping ESML files.

Tests LLM-generated ESML against the Cargo Shipping SVG board for:
  1. General ESML structural validity (envelope, IDs, cross-references)
  2. Issue A: Arrow labels must not be promoted to elements
  3. Issue B: Sequence numbers must reflect x-position, not domain logic
  4. Issue C: No orphaned aggregates or untargeted commands (original fix)

Usage:
    python validate_cargo_shipping_esml.py <esml_file.yaml>
    python validate_cargo_shipping_esml.py  # validates reference file

Exit codes: 0 = all pass, 1 = errors found, 2 = file error
"""

import sys
import yaml
from pathlib import Path
from collections import defaultdict

# ── SVG ground truth ────────────────────────────────────────────────────────
# Sticky note positions from cargo-shipping-es-board.svg (x, y, type, name)
SVG_STICKIES = {
    "Shipping Clerk":       (100, 200, "actor"),
    "Book Cargo":           (250, 200, "command"),
    "Cargo":                (250, 330, "aggregate"),
    "Cargo Booked":         (400, 200, "event"),
    "Assign Itinerary":     (550, 200, "command"),
    "Cargo Routed":         (550, 330, "event"),
    "Change Destination":   (700, 200, "command"),
    "Destination Changed":  (700, 330, "event"),
    "When Cargo Handled Derive Delivery": (850, 500, "policy"),
    "Cargo Misdirected":    (400, 500, "event"),
    "Cargo Delivered":      (550, 500, "event"),
    "Cargo Tracking View":  (1000, 200, "read_model"),
    "Routing Engine":       (1000, 330, "external"),
    "What if routing engine is unavailable?": (1000, 500, "hotspot"),
    "Port Operations":      (1400, 200, "actor"),
    "Register Handling Event": (1550, 200, "command"),
    "Cargo Received":       (1700, 200, "event"),
    "Cargo Loaded":         (1700, 330, "event"),
    "Cargo Unloaded":       (1700, 500, "event"),
    "Customs Cleared":      (1700, 670, "event"),
    "Cargo Claimed":        (1850, 200, "event"),
    "Handling Event":       (1850, 330, "aggregate"),
    "How do we handle partial unloads?": (2050, 500, "hotspot"),
    "Scheduling Dept":      (2550, 200, "actor"),
    "Schedule Voyage":      (2700, 200, "command"),
    "Voyage Scheduled":     (2700, 330, "event"),
    "Voyage Delayed":       (2700, 500, "event"),
    "Voyage":               (2850, 330, "aggregate"),
    "UN/LOCODE Port Registry": (2550, 750, "external"),
    "Should Location be external service?": (2700, 850, "hotspot"),
}

# Arrow labels (NOT stickies) — text on connectors
SVG_ARROW_LABELS = {
    "Cargo Handled": (1525, 510),  # label on arrow from (1950,520) to (1100,520)
}

# X-position groups for sequence validation
# Stickies at the same x share a sequence number
X_POSITION_GROUPS = {
    250: ["Book Cargo", "Cargo"],
    400: ["Cargo Booked", "Cargo Misdirected"],
    550: ["Assign Itinerary", "Cargo Routed", "Cargo Delivered"],
    700: ["Change Destination", "Destination Changed"],
    1550: ["Register Handling Event"],
    1700: ["Cargo Received", "Cargo Loaded", "Cargo Unloaded", "Customs Cleared"],
    1850: ["Cargo Claimed", "Handling Event"],
    2700: ["Schedule Voyage", "Voyage Scheduled", "Voyage Delayed"],
    2850: ["Voyage"],
}


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passes = []

    def error(self, category, msg):
        self.errors.append((category, msg))

    def warn(self, category, msg):
        self.warnings.append((category, msg))

    def ok(self, category, msg):
        self.passes.append((category, msg))

    def print_report(self):
        print("=" * 70)
        print("CARGO SHIPPING ESML VALIDATION REPORT")
        print("=" * 70)

        if self.passes:
            print(f"\n✓ PASSED ({len(self.passes)})")
            for cat, msg in self.passes:
                print(f"  [{cat}] {msg}")

        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)})")
            for cat, msg in self.warnings:
                print(f"  [{cat}] {msg}")

        if self.errors:
            print(f"\n✗ ERRORS ({len(self.errors)})")
            for cat, msg in self.errors:
                print(f"  [{cat}] {msg}")

        print("\n" + "=" * 70)
        total = len(self.passes) + len(self.warnings) + len(self.errors)
        print(f"Total: {len(self.passes)} passed, {len(self.warnings)} warnings, {len(self.errors)} errors / {total} checks")
        print("=" * 70)

        return len(self.errors) == 0


def load_esml(path):
    """Load and parse ESML YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def build_id_index(doc):
    """Build a dict mapping element ID -> element dict."""
    index = {}
    sections = [
        "groups", "actors", "events", "commands", "aggregates",
        "policies", "read_models", "external_systems", "hotspots",
        "opportunities", "values", "constraints", "mockups",
        "swimlanes", "unresolved",
    ]
    for section in sections:
        for elem in doc.get(section, []) or []:
            eid = elem.get("id")
            if eid:
                index[eid] = elem
    return index


def build_name_index(doc):
    """Build a dict mapping element name -> element dict."""
    index = {}
    sections = [
        "groups", "actors", "events", "commands", "aggregates",
        "policies", "read_models", "external_systems", "hotspots",
        "unresolved",
    ]
    for section in sections:
        for elem in doc.get(section, []) or []:
            name = elem.get("name")
            if name:
                index[name] = elem
    return index


def validate_envelope(doc, result):
    """Check ESML envelope fields."""
    if not doc.get("esml"):
        result.error("ENVELOPE", "Missing 'esml' version field")
    else:
        result.ok("ENVELOPE", f"ESML version: {doc['esml']}")

    board = doc.get("board", {})
    if not board.get("title"):
        result.error("ENVELOPE", "Missing board.title")
    if not board.get("variation"):
        result.error("ENVELOPE", "Missing board.variation")
    elif board["variation"] != "design_level":
        result.warn("ENVELOPE", f"Expected design_level, got {board['variation']}")
    else:
        result.ok("ENVELOPE", f"Board variation: {board['variation']}")

    sources = doc.get("sources", [])
    if not sources:
        result.error("ENVELOPE", "Missing sources section")
    else:
        result.ok("ENVELOPE", f"Sources: {len(sources)} defined")


def validate_id_conventions(doc, result):
    """Check ID prefix conventions."""
    prefix_map = {
        "events": "evt-",
        "commands": "cmd-",
        "actors": "act-",
        "aggregates": "agg-",
        "policies": "pol-",
        "read_models": "rm-",
        "external_systems": "sys-",
        "hotspots": "hot-",
        "groups": "grp-",
        "opportunities": "opp-",
        "constraints": "cst-",
    }
    all_ids = set()
    for section, prefix in prefix_map.items():
        for elem in doc.get(section, []) or []:
            eid = elem.get("id", "")
            if eid in all_ids:
                result.error("IDS", f"Duplicate ID: {eid}")
            all_ids.add(eid)
            if not eid.startswith(prefix):
                result.error("IDS", f"{eid} should start with '{prefix}'")

    if all_ids:
        result.ok("IDS", f"All {len(all_ids)} IDs checked for prefix conventions")


def validate_cross_references(doc, result):
    """Check that all cross-references resolve."""
    id_index = build_id_index(doc)
    ref_fields = [
        ("commands", "emits"),
        ("commands", "initiated_by"),
        ("commands", "targets"),
        ("aggregates", "receives"),
        ("aggregates", "produces"),
        ("policies", "listens_to"),
        ("policies", "triggers"),
        ("read_models", "informs"),
        ("read_models", "subscribes_to"),
        ("hotspots", "near"),
        ("external_systems", "receives"),
        ("external_systems", "produces"),
    ]
    broken = []
    checked = 0
    for section, field in ref_fields:
        for elem in doc.get(section, []) or []:
            val = elem.get(field)
            if val is None:
                continue
            if isinstance(val, list):
                for ref_id in val:
                    checked += 1
                    if ref_id not in id_index:
                        broken.append(f"{elem['id']}.{field} -> {ref_id}")
            elif isinstance(val, dict):
                for sub_key, ref_id in val.items():
                    if ref_id:
                        checked += 1
                        if ref_id not in id_index:
                            broken.append(f"{elem['id']}.{field}.{sub_key} -> {ref_id}")

    # Also check group references
    for section in ["events", "commands", "aggregates", "policies",
                     "read_models", "external_systems", "hotspots"]:
        for elem in doc.get(section, []) or []:
            grp = elem.get("group")
            if grp:
                checked += 1
                if grp not in id_index:
                    broken.append(f"{elem['id']}.group -> {grp}")

    if broken:
        for b in broken:
            result.error("XREF", f"Broken cross-reference: {b}")
    else:
        result.ok("XREF", f"All {checked} cross-references resolve")


def validate_element_coverage(doc, result):
    """Check that all SVG stickies are captured and none are fabricated."""
    name_index = build_name_index(doc)

    missing = []
    for name, (x, y, etype) in SVG_STICKIES.items():
        if name not in name_index:
            missing.append(f"{name} ({etype} at x={x})")

    if missing:
        for m in missing:
            result.error("COVERAGE", f"Missing element from SVG: {m}")
    else:
        result.ok("COVERAGE", f"All {len(SVG_STICKIES)} SVG stickies captured")


# ── Issue A: Arrow labels vs stickies ───────────────────────────────────────

def validate_arrow_labels_not_promoted(doc, result):
    """
    ISSUE A: Arrow labels must not become elements.
    'Cargo Handled' is text on a connector arrow, not a sticky note.
    It must NOT appear as an event, and must NOT be wired into
    listens_to/triggers on any policy.
    """
    # Check that no event named "Cargo Handled" exists
    events = doc.get("events", []) or []
    cargo_handled_events = [e for e in events
                            if "cargo" in e.get("name", "").lower()
                            and "handled" in e.get("name", "").lower()]
    if cargo_handled_events:
        for e in cargo_handled_events:
            result.error("ARROW_LABEL",
                         f"Arrow label 'Cargo Handled' promoted to event: {e['id']}. "
                         "This text is on an arrow connector, not a sticky note.")
    else:
        result.ok("ARROW_LABEL", "No phantom 'Cargo Handled' event created")

    # Check that the policy's listens_to does not fabricate connections
    policies = doc.get("policies", []) or []
    for pol in policies:
        if "derive" in pol.get("name", "").lower() or "handled" in pol.get("name", "").lower():
            listens_to = pol.get("listens_to", []) or []
            if listens_to:
                result.error("ARROW_LABEL",
                             f"Policy {pol['id']} has listens_to={listens_to}. "
                             "The triggering event 'Cargo Handled' is an arrow label, "
                             "not a sticky — it should be in unresolved, not decomposed "
                             "into individual event references.")
            else:
                result.ok("ARROW_LABEL",
                          f"Policy {pol['id']} correctly has no listens_to "
                          "(trigger is an arrow label, not a sticky)")

    # Check that 'Cargo Handled' appears in unresolved
    unresolved = doc.get("unresolved", []) or []
    cargo_handled_unresolved = [u for u in unresolved
                                 if "cargo" in (u.get("text_raw", "") or u.get("name", "")).lower()
                                 and "handled" in (u.get("text_raw", "") or u.get("name", "")).lower()]
    if cargo_handled_unresolved:
        result.ok("ARROW_LABEL",
                  "Arrow label 'Cargo Handled' correctly captured in unresolved section")
    else:
        result.error("ARROW_LABEL",
                     "'Cargo Handled' arrow label not found in unresolved section. "
                     "Arrow labels that don't correspond to stickies must be captured "
                     "in unresolved with suspected_type.")


# ── Issue B: Sequence = x-position ──────────────────────────────────────────

def validate_sequence_by_position(doc, result):
    """
    ISSUE B: Sequence numbers must reflect horizontal (x) position on the
    board, not domain-logical ordering.

    Key test: evt-cargo-misdirected (x=400) and evt-cargo-delivered (x=550)
    must have the SAME sequence numbers as other elements at those x-positions,
    not higher numbers based on when they happen in the domain.
    """
    name_index = build_name_index(doc)

    # Test case: Cargo Misdirected (x=400) vs Cargo Booked (x=400)
    misdirected = name_index.get("Cargo Misdirected", {})
    booked = name_index.get("Cargo Booked", {})
    if misdirected and booked:
        m_seq = misdirected.get("sequence")
        b_seq = booked.get("sequence")
        if m_seq is not None and b_seq is not None:
            if m_seq == b_seq:
                result.ok("SEQUENCE",
                          f"Cargo Misdirected (seq={m_seq}) matches Cargo Booked "
                          f"(seq={b_seq}) — same x-position (400)")
            else:
                result.error("SEQUENCE",
                             f"Cargo Misdirected (seq={m_seq}) != Cargo Booked "
                             f"(seq={b_seq}). Both are at x=400 — sequence must "
                             "reflect board position, not domain-logical order.")

    # Test case: Cargo Delivered (x=550) vs Cargo Routed (x=550)
    delivered = name_index.get("Cargo Delivered", {})
    routed = name_index.get("Cargo Routed", {})
    if delivered and routed:
        d_seq = delivered.get("sequence")
        r_seq = routed.get("sequence")
        if d_seq is not None and r_seq is not None:
            if d_seq == r_seq:
                result.ok("SEQUENCE",
                          f"Cargo Delivered (seq={d_seq}) matches Cargo Routed "
                          f"(seq={r_seq}) — same x-position (550)")
            else:
                result.error("SEQUENCE",
                             f"Cargo Delivered (seq={d_seq}) != Cargo Routed "
                             f"(seq={r_seq}). Both are at x=550 — sequence must "
                             "reflect board position, not domain-logical order.")

    # Test case: all x=1700 events share a sequence
    x1700_events = ["Cargo Received", "Cargo Loaded", "Cargo Unloaded", "Customs Cleared"]
    x1700_seqs = set()
    for name in x1700_events:
        elem = name_index.get(name, {})
        seq = elem.get("sequence")
        if seq is not None:
            x1700_seqs.add(seq)
    if len(x1700_seqs) == 1:
        result.ok("SEQUENCE",
                  f"All x=1700 tracking events share sequence={x1700_seqs.pop()}")
    elif len(x1700_seqs) > 1:
        result.error("SEQUENCE",
                     f"Tracking events at x=1700 have different sequences: "
                     f"{x1700_seqs}. Vertically aligned events must share "
                     "a sequence number.")

    # General: sequences must be monotonically non-decreasing with x-position
    events = doc.get("events", []) or []
    commands = doc.get("commands", []) or []
    sequenced = []
    for elem in events + commands:
        seq = elem.get("sequence")
        bbox = (elem.get("origin") or {}).get("bbox")
        if seq is not None and bbox:
            x_pos = bbox[0]
            sequenced.append((x_pos, seq, elem.get("name", elem.get("id"))))

    sequenced.sort(key=lambda t: t[0])  # sort by x-position
    violations = []
    for i in range(1, len(sequenced)):
        prev_x, prev_seq, prev_name = sequenced[i - 1]
        curr_x, curr_seq, curr_name = sequenced[i]
        if curr_x > prev_x and curr_seq < prev_seq:
            violations.append(
                f"{curr_name} (x={curr_x}, seq={curr_seq}) has lower sequence "
                f"than {prev_name} (x={prev_x}, seq={prev_seq})")

    if violations:
        for v in violations:
            result.error("SEQUENCE", f"Sequence/position mismatch: {v}")
    else:
        result.ok("SEQUENCE",
                  "All sequence numbers are consistent with x-positions")


# ── Issue C: No orphaned aggregates ─────────────────────────────────────────

def validate_no_orphaned_aggregates(doc, result):
    """
    ISSUE C (original fix): Aggregates must not have empty receives/produces
    when commands and events exist in the same group.
    """
    aggregates = doc.get("aggregates", []) or []
    commands = doc.get("commands", []) or []
    events = doc.get("events", []) or []

    # Build group -> elements index
    group_commands = defaultdict(list)
    group_events = defaultdict(list)
    for cmd in commands:
        grp = cmd.get("group")
        if grp:
            group_commands[grp].append(cmd)
    for evt in events:
        grp = evt.get("group")
        if grp:
            group_events[grp].append(evt)

    for agg in aggregates:
        agg_id = agg.get("id", "unknown")
        grp = agg.get("group")
        receives = agg.get("receives", []) or []
        produces = agg.get("produces", []) or []

        if not receives and grp in group_commands:
            result.error("ORPHAN",
                         f"Aggregate {agg_id} has empty 'receives' but group "
                         f"{grp} contains commands: "
                         f"{[c['id'] for c in group_commands[grp]]}")
        elif receives:
            result.ok("ORPHAN", f"Aggregate {agg_id} receives: {receives}")

        if not produces and grp in group_events:
            result.error("ORPHAN",
                         f"Aggregate {agg_id} has empty 'produces' but group "
                         f"{grp} contains events: "
                         f"{[e['id'] for e in group_events[grp]]}")
        elif produces:
            result.ok("ORPHAN", f"Aggregate {agg_id} produces: {produces}")


def validate_no_untargeted_commands(doc, result):
    """
    ISSUE C (original fix): Commands in a group with an aggregate must
    have a targets field.
    """
    commands = doc.get("commands", []) or []
    aggregates = doc.get("aggregates", []) or []

    group_aggs = defaultdict(list)
    for agg in aggregates:
        grp = agg.get("group")
        if grp:
            group_aggs[grp].append(agg)

    for cmd in commands:
        cmd_id = cmd.get("id", "unknown")
        grp = cmd.get("group")
        targets = cmd.get("targets")

        if not targets and grp in group_aggs:
            result.error("UNTARGETED",
                         f"Command {cmd_id} has no 'targets' but group {grp} "
                         f"contains aggregates: "
                         f"{[a['id'] for a in group_aggs[grp]]}")
        elif targets:
            result.ok("UNTARGETED", f"Command {cmd_id} targets: {targets}")


# ── Main ────────────────────────────────────────────────────────────────────

def validate(path):
    """Run all validations on an ESML file."""
    print(f"Validating: {path}\n")

    try:
        doc = load_esml(path)
    except Exception as e:
        print(f"ERROR: Failed to load ESML file: {e}")
        return False

    result = ValidationResult()

    # Structural checks
    validate_envelope(doc, result)
    validate_id_conventions(doc, result)
    validate_cross_references(doc, result)
    validate_element_coverage(doc, result)

    # Issue-specific checks
    validate_arrow_labels_not_promoted(doc, result)   # Issue A
    validate_sequence_by_position(doc, result)          # Issue B
    validate_no_orphaned_aggregates(doc, result)        # Issue C
    validate_no_untargeted_commands(doc, result)        # Issue C

    return result.print_report()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Default: validate the reference file
        script_dir = Path(__file__).parent
        target = script_dir / "files" / "cargo-shipping-es-board-reference.esml.yaml"

    if not Path(target).exists():
        print(f"ERROR: File not found: {target}")
        sys.exit(2)

    success = validate(target)
    sys.exit(0 if success else 1)

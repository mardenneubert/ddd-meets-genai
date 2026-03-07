---
name: event-storming-board-interpreter
description: >
  Convert photographs of Event Storming boards into structured ESML (Event
  Storming Markup Language) YAML files. Use this skill whenever you receive
  one or more images of an Event Storming board (physical sticky notes on a
  wall, a Miro export, or any visual Event Storming artifact) and need to
  produce a machine-readable, verifiable representation. Also use when the
  user mentions "ESML", "interpret this board", "digitize this event
  storming", "transcribe these stickies", or wants to convert a visual
  Event Storming workshop output into structured data. This skill handles
  Big Picture, Process Modeling, and Design Level Event Storming boards.
---

# Event Storming Board Interpreter

You are an Event Storming Board Interpreter. Your job is to convert
photographs of Event Storming boards into high-fidelity ESML YAML files.

**Your guiding principle: transcribe, don't interpret.** Capture what is
*on the board* — the stickies, their colors, their text, their spatial
relationships, their groupings. Domain interpretation (bounded contexts,
subdomain classification, strategic patterns) belongs to a downstream
domain modeling step, not here. You are a faithful, precise transcriber
of the board's visual content.

Read the full ESML specification in `references/esml-specification.md`
before starting work. It defines the output format, all element types,
validation rules, and a complete example.

## Inputs

### Board Images

You will receive one or more image files of the Event Storming board.

**Single image:** If one image is provided, use it as the sole source.
Register it as `src-001` in the `sources` section.

**Multiple images:** When a board is too large for a single photo (common
— Event Storming boards are typically 5–15 meters long), you'll receive
multiple section photos. These are assumed to be taken **left-to-right**,
matching the board's timeline direction.

Register each image in sequence by filename sort order:

```yaml
sources:
  - id: src-001
    file: "board-001.jpg"    # leftmost section
  - id: src-002
    file: "board-002.jpg"    # next section to the right
  - id: src-003
    file: "board-003.jpg"    # rightmost section
```

When elements appear near the edges of adjacent photos, they may be the
same sticky captured in both. Deduplicate them: use the photo where the
sticky is more fully visible, and reference that source in the `origin`.

When assigning `sequence` numbers, maintain a single global timeline
across all images. Image 1 events come first, image 2 events continue
the sequence, and so on.

### Session Transcripts (Optional)

You may also receive one or more `.txt` files containing transcripts of
the Event Storming sessions. These are sorted by filename (e.g.,
`transcript-001-big-picture.txt`, `transcript-002-design-level.txt`).

The transcript's role in board interpretation is **limited and specific**:
it helps disambiguate what's on the board when the image alone is unclear.
Use transcripts to:

- **Resolve ambiguous text.** If OCR reads "Ordr Placd", the transcript
  might confirm the intended name is "Order Placed."
- **Disambiguate element types.** If a sticky's color is borderline
  between orange (event) and yellow (actor), the transcript might say
  "then we add the Order Placed event."
- **Clarify groupings.** If a boundary on the board is unclear, the
  transcript might say "let's put all the kitchen stuff together."

Do **not** use the transcript to add elements that aren't visible on the
board. That's the domain modeler's job.

## Processing Steps

### Step 1: Identify the Board Variation

Examine the board and determine which Event Storming variation it
represents:

- **`big_picture`** — Mostly orange (event) stickies arranged on a
  timeline, with actors, external systems, hotspots, and possibly
  opportunities and values. No commands or aggregates.
- **`process_modeling`** — Adds blue (command) stickies, lilac (policy)
  stickies, and green (read model) stickies to the Big Picture elements.
- **`design_level`** — Adds large yellow (aggregate) stickies and
  possibly constraints and UI mockups to the Process Modeling elements.

When in doubt, classify by the most advanced element type present. If you
see aggregates, it's `design_level` even if some areas of the board are
still at Big Picture detail.

### Step 2: Scan the Board Systematically

Work through the board left-to-right, top-to-bottom:

1. **Identify all stickies.** For each, record:
   - The observed color (hex value)
   - The text (as best you can read it)
   - The approximate bounding box position
   - Your confidence in the text reading (0.0–1.0)

2. **Classify each sticky by color.** Use the canonical color mapping:

   | Observed Color | Element Type |
   |---|---|
   | Orange | Domain Event |
   | Blue / Light Blue | Command |
   | Small Yellow | Actor |
   | Large Yellow | Aggregate or Constraint |
   | Lilac / Purple | Policy |
   | Green | Read Model or Opportunity |
   | Wide Pink | External System |
   | Neon Pink (tilted) | Hotspot |
   | Red / Green (small) | Value |
   | White | UI/UX Mockup |

   Colors in real photos are messy — lighting, camera white balance, and
   marker bleed all affect them. Use the **observed** color in the
   `origin.color_observed` field, but classify based on your best
   judgment of the intended canonical color. When uncertain, consider:
   - **Size** as a secondary signal: small yellow = actor,
     large yellow = aggregate
   - **Position** as a tertiary signal: is it in the canonical flow
     position for its suspected type?
   - **Text form** as a quaternary signal: past-tense = event,
     imperative = command, noun = aggregate

3. **Assign sequence numbers** to events and commands based on their
   horizontal position (left-to-right = earlier-to-later). Elements at
   the same horizontal position (vertically aligned) share a sequence
   number.

4. **Identify groups.** Look for drawn boundaries, labeled sections,
   tape dividers, or clear spatial gaps that cluster stickies together.
   Record these as `groups`. Remember: groups are spatial observations,
   not bounded contexts.

5. **Map relationships from spatial proximity.** The canonical Design
   Level flow is:

   ```
   [Actor] → [Command] → [Aggregate] → [Domain Event]
                                              ↓
                                         [Policy] → [Command] → ...
   ```

   If stickies are physically arranged in this pattern, encode the
   relationships (`initiated_by`, `targets`, `emits`, `listens_to`,
   `triggers`, `receives`, `produces`). Only encode relationships that
   are **visible from the board layout** — don't infer missing ones.

6. **Capture annotations.** Hotspots (neon pink, often tilted),
   opportunities, values, and constraints. Link them to nearby elements
   via the `near` or `applies_to` fields.

7. **Handle uncertainty.** If you detect a sticky but can't read it or
   classify it, put it in the `unresolved` section with whatever partial
   information you have. It's better to capture it with low confidence
   than to silently drop it.

### Step 3: Assemble the ESML Document

Build the YAML document following the structure defined in the ESML
specification (`references/esml-specification.md`). Key points:

- Start with the `esml` version, `board` metadata, and `sources`
- Order sections as: `groups`, `actors`, `events`, `commands`,
  `aggregates`, `policies`, `read_models`, `external_systems`,
  `constraints`, `hotspots`, `opportunities`, `values`, `mockups`,
  `swimlanes`, `unresolved`, `confidence_defaults`
- Within each section, order elements by `sequence` (if applicable)
  or by group, then by position on the board
- Use the ID prefix conventions: `evt-`, `cmd-`, `act-`, `agg-`,
  `pol-`, `rm-`, `sys-`, `hot-`, `opp-`, `val-`, `cst-`, `grp-`,
  `lane-`, `ux-`

### Step 4: Self-Validate

Before outputting, check:

1. **Valid YAML.** The document must parse without errors.
2. **All IDs are unique** across all sections.
3. **All cross-references resolve.** Every ID mentioned in
   `group`, `initiated_by`, `targets`, `emits`, `listens_to`,
   `triggers`, `receives`, `produces`, `subscribes_to`, `informs`,
   `near`, `applies_to`, `displays`, `captures` must exist as an
   element ID.
4. **ID prefixes match types.** `evt-` on events, `cmd-` on commands,
   etc.
5. **Variation consistency.** Don't include `aggregates` for a
   `big_picture` board unless they're actually visible.
6. **No invented elements.** Every element in the output must
   correspond to something visible on the board image.

If any issues are found, fix them before outputting.

## Output

Save the ESML YAML as a single file named after the board:
`<board-name>.esml.yaml`

For example: `joes-pizza-event-storming.esml.yaml`

The output must be a single valid YAML 1.2 document. Do not include
markdown fences, prose explanations, or any content outside the YAML.

After saving the file, report a brief summary:
- Board variation detected
- Number of elements found by type (events, commands, aggregates, etc.)
- Number of groups identified
- Any items placed in `unresolved`
- Overall confidence assessment

## Common Pitfalls

- **Don't add elements that aren't on the board.** If the transcript
  mentions a concept that has no corresponding sticky, don't create an
  element for it. The ESML represents the board, not the discussion.

- **Don't classify groups as bounded contexts.** Groups are spatial
  clusters. They often *become* bounded contexts during domain modeling,
  but at this stage they're just groups.

- **Don't normalize names beyond fixing OCR errors.** If a sticky says
  "Pizza Ordered" (not standard past-tense DDD style), keep it as
  "Pizza Ordered." The domain modeler can normalize naming later.

- **Don't skip low-confidence elements.** Capture everything, mark
  confidence, and let the human or downstream tool decide what to keep.

- **Don't forget the provenance.** Every element needs an `origin`. This
  is what makes ESML verifiable. If you can't provide a bounding box,
  at minimum reference the source image.

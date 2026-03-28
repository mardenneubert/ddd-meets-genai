# Information Loss: DMML → Mermaid

This document catalogs DMML elements and attributes that **cannot be fully
represented** in Mermaid diagrams, along with the mitigation strategy for each.

The goal is transparency: users should know exactly what survives the
transformation and what gets reduced or lost.

## Fully Representable (No Loss)

These DMML elements map directly to Mermaid constructs:

| DMML Element | Mermaid Representation |
|---|---|
| Bounded contexts | Context map nodes; class diagram grouping |
| Context map relationships | Flowchart edges with labels |
| Aggregate root entities | Classes with `<<Aggregate Root>>` |
| Child entities | Classes with `<<Entity>>` |
| Value objects | Classes with `<<Value Object>>` |
| Entity/VO attributes | Class attributes with types |
| Nullable attributes | `?` suffix on attribute |
| Lifecycle states | State diagram states + transitions |
| Commands | Classes with `<<Command>>` |
| Domain events | Classes with `<<Domain Event>>` |
| Command → event (emits) | Dashed arrow with label |
| Policies | Classes with `<<Policy>>` |
| Policy trigger events | Dashed arrow with "triggers" label |
| Policy issued commands | Dashed arrow with "issues" label |
| Read models | Classes with `<<Read Model>>` |
| Read model attributes | Class attributes |
| Read model subscriptions | Dashed arrows from events |
| Domain services | Classes with `<<Domain Service>>` |
| Service operations | Class methods |
| Repositories | Classes with `<<Repository>>` |
| Repository operations | Class methods |
| Factories | Classes with `<<Factory>>` |
| Specifications | Classes with `<<Specification>>` |
| Composition (within aggregate) | `*--` relationship |
| Cross-aggregate references | `-->` relationship |
| Subdomain classification | Flowchart subgraph styling |
| External BCs | Dashed-border nodes |
| Integration style | Edge label on context map |
| Relationship type | Edge label on context map |
| Process manager states | State diagram |
| Process manager transitions | State transitions with labels |

## Partially Representable (Reduced)

These elements are captured but in a simplified form:

| DMML Element | What's Kept | What's Lost | Mitigation |
|---|---|---|---|
| **Invariants** | Listed as bullet points in a note | Full natural-language detail may be truncated | Kept in `%%` comment if note too long |
| **Command preconditions** | Listed as bullet points in a note | Full detail truncated | Kept in `%%` comment |
| **Specification predicate** | Name + brief note | Full predicate expression | Full predicate in `%%` comment |
| **Entity identity (generation)** | Attribute type shown | `generation` strategy (system/user/external) not visualized | Added as `%%` comment |
| **Value object equality** | Stereotype implies all-attributes | `equality: subset` not distinguishable from `all_attributes` | Note added when `subset` |
| **Lifecycle transitions** | Inferred from commands/events | Explicit transition guards not in DMML | Inferred transitions marked with `%%` comment |
| **Event consumed_by** | Listed in `%%` comments | Not a visual edge (cross-BC) | Comment preserves the data |
| **Subdomain business_value** | Not shown | Too verbose for diagram | Preserved as `%%` comment |
| **Application service coordinates** | Shown as `-->` to repos/services | The "orchestration" semantics not visual | Relationship labels help |
| **Process manager timeout** | Note on state | Duration/action detail may be truncated | Full detail in `%%` comment |
| **Process manager compensation** | Note on terminal state | Full strategy text truncated | Full text in `%%` comment |

## Not Representable (Preserved as Comments Only)

These DMML elements have no visual equivalent in Mermaid and are preserved
solely as `%%` comments in the output:

| DMML Element | Why It Can't Be Shown | Where the Comment Goes |
|---|---|---|
| **model.description** | Free-form prose, too long | Top of file |
| **model.notes** | Free-form prose, too long | Top of file |
| **model.authors** | Metadata | Top of file |
| **model.date** | Metadata | Top of file |
| **model.esml_source** | Metadata | Top of file |
| **Element status** (draft/proposed/accepted) | No visual encoding — Mermaid has no dashed-class-border concept | Comment on each element |
| **Element notes** | Free-form rationale text per element | Comment near the element |
| **Element description** | Free-form text per element | Comment near the element |
| **Ubiquitous language terms** | Glossary definitions, no diagram equivalent | Block of comments in the BC's aggregate structure diagram |
| **BC responsibilities** | Bullet list, no diagram equivalent | Comment in context map |
| **Module containment** | Mermaid namespaces can't hold relationships | Comment listing which module contains which elements |
| **Subdomain description** | Prose text | Comment in context map |
| **Context map description/notes** | Prose text | Comment at top of context map |
| **Relationship description/notes** | Prose text | Comment near the relationship edge |

## Design Decisions

1. **Comments over omission.** The output file is a lossless encoding of the
   DMML — every piece of information appears, either visually or as a `%%`
   comment. This means the .md file can serve as a reference even beyond what
   the rendered diagrams show.

2. **Notes for important constraints.** Invariants and preconditions are
   important enough to appear as visible notes on the diagram, even if
   truncated. The full text goes in a comment immediately above the note.

3. **Status is always a comment.** There's no clean way to visually encode
   draft/proposed/accepted in Mermaid without making diagrams cluttered.
   Status goes in a comment on every element.

4. **Ubiquitous language gets a dedicated comment block.** Since it's a
   glossary that doesn't map to any diagram construct, it's placed as a
   block of comments at the top of the BC's aggregate structure diagram.

# Domain Modeling Meets Generative AI

**Turning domain conversations into structured, machine-readable models with AI agents that understand DDD.**

This repository contains the specifications, AI agent skills, and evaluation cases from our ongoing research into the intersection of Domain-Driven Design and Generative AI. The core idea: domain knowledge captured in Event Storming workshops can be systematically transformed into verified domain models by LLM-powered agents, bridging the gap between collaborative domain discovery and software implementation.

[XP 2026 Slides](<Domain Modeling Meets GenAI-XP2026.pdf>)

---

## The Problem

Domain-Driven Design has a knowledge bottleneck. Event Storming sessions produce rich, nuanced understanding of a domain — but that knowledge lives on sticky notes, whiteboards, and in people's heads. Translating it into actionable domain models (bounded contexts, aggregates, entities, value objects, context maps) is manual, error-prone, and often skipped entirely. Teams go straight from user stories to code, losing the strategic design that DDD promises.

## Our Approach

We propose a spec-driven pipeline where domain knowledge flows through structured, machine-readable formats:

**Conversation → Board → ESML → DMML → Code**

Each step has a defined specification and an AI agent skill that performs the transformation:

1. **Event Storming workshops** capture domain knowledge through facilitated conversations with domain experts
2. **Board images** (photos, Miro exports) are the raw artifact from those sessions
3. **ESML** (Event Storming Markup Language) is a faithful, high-fidelity transcription of what's on the board — stickies, colors, positions, groupings — without interpretation
4. **DMML** (Domain Model Markup Language) interprets the ESML into a strategic and tactical DDD domain model — subdomains, bounded contexts, aggregates, entities, value objects, events, commands, policies, and more
5. **Code scaffolds** (future work) can be generated from the tactical DMML model

The specifications (ESML and DMML) are the backbone. They define YAML formats that are simultaneously human-readable, LLM-friendly, and machine-validatable. Every element carries provenance (`notes` explaining *why*), confidence tracking, and progressive elaboration through `status` fields (`draft` → `proposed` → `accepted`).

## Why Agent Skills?

The transformations in this pipeline are packaged as **agent skills** — self-contained instruction sets that any compatible LLM coding agent (Claude Code, Cursor, GitHub Copilot, etc.) can execute. Skills are more than prompts: they include the full specification as reference material, validation scripts, and evaluation cases with known-good reference outputs.

This design choice matters because:

- **Reproducibility.** Given the same inputs, different runs should produce structurally similar outputs. The specs constrain the output space enough that LLM variability becomes manageable.
- **Evaluability.** Reference outputs for each domain case let us measure how well an LLM performs the transformation, catching hallucinations (fabricated elements), omissions, and misclassifications.
- **Portability.** Skills aren't locked to a single LLM or tool. Any agent that can read a SKILL.md file and follow instructions can run the pipeline.
- **Progressive improvement.** As LLMs improve, the same skills produce better outputs — no code changes needed, just better models running the same specs.

---

## Repository Structure

```
ddd-meets-genai/
├── ESML-Specification-Draft.md          # Event Storming Markup Language v0.2.1
├── DMML-Specification-Draft.md          # Domain Model Markup Language v0.1.0
│
└── skills/
    ├── event-storming-board-interpreter/
    │   ├── SKILL.md                     # Agent instructions for board → ESML
    │   ├── references/                  # ESML spec (bundled with the skill)
    │   ├── scripts/                     # Validation scripts
    │   └── evals/files/                 # Evaluation cases
    │       ├── cargo-shipping/          # Synthetic case (SVG + reference ESML)
    │       ├── bringots/                # Exercise case (SVG + reference ESML)
    │       └── joes-pizza/              # Real case (PNG + reference ESML)
    │
    └── domain-modeler/
        ├── SKILL.md                     # Agent instructions for ESML+transcripts → DMML
        ├── references/                  # ESML + DMML specs (bundled)
        ├── scripts/                     # DMML validator
        └── evals/files/                 # Evaluation cases
            ├── cargo-shipping/          # ESML + transcript + reference DMML
            ├── bringots/                # ESML + transcript + reference DMML
            └── joes-pizza/              # ESML + 2 transcripts + reference DMML
```

## Evaluation Cases

Each skill includes evaluation cases at increasing levels of complexity:

| Domain | Type | Source | Complexity |
|---|---|---|---|
| **Cargo Shipping** | Synthetic | Generated SVG board based on Eric Evans' classic DDD example | Baseline — well-known domain, clean synthetic board |
| **Bringots** | Exercise | Credit card services for a fictional Brazilian bank, from a workshop exercise | Medium — multiple bounded contexts, complex lifecycle, external systems |
| **Joe's Pizza** | Real | Actual Miro board + recorded workshop transcripts from two Event Storming sessions | High — real-world ambiguity, floating aggregates, concurrent events, duplicate stickies |

---

## Specifications

### ESML — Event Storming Markup Language (v0.2.1)

A YAML format for transcribing Event Storming boards. Captures events, commands, aggregates, actors, policies, read models, external systems, hotspots, and unresolved items — with spatial metadata (bounding boxes, colors), sequence numbering, and confidence scores. The guiding principle is *transcribe, don't interpret*: ESML captures what's on the board, not what it means.

### DMML — Domain Model Markup Language (v0.1.0)

A YAML format for machine-readable DDD domain models. Covers both strategic design (subdomains with classification, bounded contexts with responsibilities, context map with relationship types) and tactical design (aggregates, root entities, child entities, value objects, domain events, commands, policies, process managers, repositories, factories, specifications, read models, modules, ubiquitous language). Every element carries `status` and `notes` fields for progressive elaboration and traceable reasoning.

---

## About the Authors

### Marden Neubert

Technology executive, author, and speaker with over 20 years of experience in software engineering, distributed systems, and complex domain modeling. Former CTO at PagSeguro (Brazil's largest independent payments company) and former CEO at UOL BoaCompra. Holds BSc and MSc in Computer Science from UFMG. Teaches Agile Processes in the MBA program at FIAP. His research interests include resilient architectures, modeling of complex domains, and the application of generative AI to software engineering practices.

### Joseph (Joe) W. Yoder

Internationally recognized software architect, pattern author, and President of The Hillside Group. Founder and principal of The Refactory, Inc. Co-author of the seminal *Big Ball of Mud* pattern (with Brian Foote, 1997), which remains one of the most cited works in software architecture. A leading voice in the patterns community for over 25 years, Joe has organized and presented at conferences worldwide including PLoP, EuroPLoP, OOPSLA/SPLASH, QCon, GOTO, and YOW!. His work on Adaptive Object Models, architecture patterns, and bounded agent design bridges classical software engineering with emerging AI-driven approaches.

### Collaboration

Marden and Joe have been collaborating on software architecture patterns since 2022, including the *Leading a Software Architecture Revolution* pattern series presented at EuroPLoP 2023 and *Architecting Agility* at Agile Brazil. Their *Domain Modeling Meets Generative AI* research was first presented at Agile Brazil 2025 (Florianópolis) and continues at XP 2026 (São Paulo, April 2026).

---

## Presentations

- **Agile Brazil 2025** (Rio de Janeiro, September 2025) — *Domain Modeling Meets Generative AI.* First public presentation of the ESML/DMML pipeline with manual prompt orchestration and the Joe's Pizza case study.
- **XP 2026** (São Paulo, April 2026) — *Domain Modeling Meets Generative AI.* Updated with agent skills, evaluation framework, spec-driven development framing, and the Bringots case study.

---

## Status

This is active research. The specifications, skills, and evaluation cases are evolving. Contributions, feedback, and new domain cases are welcome.

**Current focus areas:**

- Improving LLM reliability on ESML transcription (reducing hallucinated elements, improving spatial accuracy)
- Expanding DMML coverage (process managers, sagas, specifications)
- Adding a code generation skill (DMML → aggregate root classes, event definitions, repository interfaces)
- Benchmarking across LLMs (Claude, GPT, Gemini) using the evaluation framework

## License

MIT — see [LICENSE](LICENSE).

## Citation

If you reference this work, please cite:

> Neubert, M. & Yoder, J. (2025). *Domain Modeling Meets Generative AI.* Agile Brazil 2025, Rio de Janeiro, Brazil.

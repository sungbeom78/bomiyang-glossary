```md
# BomTS Glossary

> A word-based glossary system that enforces consistent naming across codebases, with AI-powered enrichment and multi-language support.

🌐 Languages:
- 🇺🇸 English (Current)
- 🇰🇷 [Korean](README.ko.md)

---

## What is this?

BomTS Glossary is a **word-level naming system** designed to eliminate inconsistency in identifiers across large-scale systems.

Instead of allowing arbitrary naming like:

```

get_position / fetch_position / load_position

```

You define a single base concept:

```

position

```

And enforce consistent usage:

```

get_position

```

All identifiers must be composed from a controlled vocabulary.

---

## Why this matters

In real-world systems:

- Naming becomes inconsistent over time
- AI-generated code introduces duplicate concepts
- Code navigation becomes harder
- Team communication breaks down

This system solves those problems by:

- Enforcing a shared vocabulary (`words.json`)
- Validating identifiers automatically
- Preventing duplicate naming patterns
- Guiding AI agents to generate consistent code

---

## Who should use this?

This system is especially useful if:

- You are building a large or long-lived system
- You use AI coding tools (Codex, Claude, Gemini, etc.)
- Naming consistency is important for your architecture
- You want to standardize terminology across a team

---

## When NOT to use this

You probably don’t need this if:

- Your project is small or short-lived
- You are working solo without naming complexity
- You don’t care about naming consistency or structure

---

## Core Concept

```

words.json       → atomic building blocks
compounds.json   → special cases
terms.json       → auto-generated (read-only)

```

All identifiers must be built from registered words.

---

## Architecture

```

code
→ scan_items
→ batch_items
→ review (Web UI)
→ words.json

→ generate_glossary
→ terms.json / GLOSSARY.md

````

---

## Quick Start

```bash
# validate + generate
python glossary/bin/run.py

# check identifier
python glossary/generate_glossary.py check-id kill_switch
````

---

## Web UI

```bash
python glossary/web/server.py
```

→ [http://localhost:5000](http://localhost:5000)

Use the UI for:

* Reviewing batch results
* Registering new words safely
* Managing glossary entries

---

## Word Registration Flow

1. Run `check-id`
2. Identify missing words
3. Register new words (via UI or CLI)
4. (Optional) Register compound terms
5. Generate glossary

---

## Auto Enrichment

```bash
python glossary/bin/enrich_items.py
```

Enrichment follows a strict policy:

1. **Dictionary first**
2. **AI fallback**
3. **Non-destructive updates**

This ensures:

* Reliable definitions
* Multi-language support
* Minimal manual effort

---

## Example Workflow

```text
New identifier → check-id
→ missing word detected
→ register word
→ generate glossary
→ validated identifier ready
```

---

## Design Principles

* **Word-first, not term-first**
* **Dictionary → AI fallback**
* **Non-destructive updates**
* **Concept-based descriptions**
* **Consistency over flexibility**

---

## Notes

* `terms.json` is auto-generated (do not edit)
* Use Web UI for safe batch operations
* CLI `auto` mode applies changes immediately

---

## License / Usage

Internal tool for the BomTS ecosystem.
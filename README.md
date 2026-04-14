# BOM_TS Glossary

> A self-evolving glossary system powered by AI, supporting multi-language definitions and automated word enrichment.

🌐 Languages:
- 🇺🇸 English (Current)
- 🇰🇷 [Korean](README.ko.md)

---

## What is this?

BOM_TS Glossary is a **word-level naming system** that ensures all identifiers are built from a controlled vocabulary.

Instead of:
```
get_position / fetch_position / load_position
```

You define:
```
position
```

And enforce:
```
get_position
```

---

## Why it matters

In large systems:

- Naming becomes inconsistent
- AI agents generate duplicate logic
- Code navigation becomes difficult

This system solves that by:

- Enforcing a shared vocabulary (`words.json`)
- Validating identifiers automatically
- Enabling AI agents to generate consistent code

---

## Core Concept

```
words.json → building blocks
compounds.json → special cases
terms.json → auto-generated (read-only)
```

All identifiers must be composed of registered words.

---

## Architecture

```
code → scan_items → batch_items → review → words.json
↓
generate_glossary
↓
terms.json / GLOSSARY.md
```

---

## Quick Start

```bash
# validate + generate
python glossary/bin/run.py

# check identifier
python glossary/generate_glossary.py check-id kill_switch
```

---

## Web UI

```bash
python glossary/web/server.py
```

→ [http://localhost:5000](http://localhost:5000)

---

## Word Registration Flow

1. Run `check-id` against your terminology
2. Register missing words
3. (Optional) Register compound variations
4. Generate the final glossary

---

## Auto Enrichment

```bash
python glossary/bin/enrich_items.py
```

* Dictionary first
* AI fallback
* Multi-language support

---

## Design Principles

* **Word-first** (not term-first)
* **Dictionary** → AI fallback
* **Non-destructive** updates
* **Concept-based** descriptions

---

## Notes

* `terms.json` is auto-generated (do not edit)
* Use Web UI for safe batch operations
* CLI auto mode applies changes immediately

---

## License / Usage

Internal tool for BOM_TS ecosystem.

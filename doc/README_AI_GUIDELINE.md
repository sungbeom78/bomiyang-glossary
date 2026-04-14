# AI Guideline

This document serves as the AI guideline for the BOM_TS glossary submodule.

## Configuration Guidelines
- Environment variables and credentials must not be hardcoded in the source code.
- Always use the `.env` file (via `scan_terms.load_env`) for environment configurations (such as API keys `ANTHROPIC_API_KEY`, etc.).
- Base configuration defaults such as `MAX_OUTPUT_TOKENS` and `BATCH_CHUNK_SIZE` can be overridden in the `.env` file. No environment-specific values should be checked into version control. Ensure all secrets are loaded dynamically.

## Naming Standards 
- System ID: BOM_TS
- Folders: Singular form only (`test/`, `log/`, etc.) per AGENTS.md.
- New identifier terminology must be checked with `python glossary/generate_glossary.py check-id <identifier>`.
- Run `python glossary/generate_glossary.py generate` before agent-assisted naming work so `build/index/word_min.json` and `build/index/variant_map.json` are current.
- When providing glossary context to AI agents, prefer `build/index/word_min.json` first. It is the sparse runtime index and now carries `id`, `lang`, `domain`, `status`, and `canonical_pos` for naming-gate decisions.
- Python Scripts: `snake_case.py`
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Documentation Rules
- `doc/` directory is the single source of truth for architecture and documentation.
- `module_index.md` and `change_log.md` must be kept up to date upon any changes.
- Document paths, class names, function names, responsibilities, and data flow.

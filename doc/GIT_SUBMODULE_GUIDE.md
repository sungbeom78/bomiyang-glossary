# Glossary Git Submodule Guide

This document outlines how to integrate and use the `glossary` submodule in external Python/Data projects.
The `glossary` submodule is designed to be completely independent, maintaining a single-source-of-truth vocabulary that any attached project can consume to strictly enforce naming conventions.

---

## 1. Submodule Philosophy and Boundary

1. **Standalone & Independent**: The glossary module does not depend on, nor should it import from, any parent project's logic, config, or `.env` files.
2. **Read APIs only**: Parent projects must never attempt to parse the `json` files in `glossary/dictionary/` manually.
3. **Write Protection**: Any new terms, edits, or removals must go through `GlossaryWriter` or the built-in generator script. External scripts shouldn't rewrite JSON files directly.

## 2. Integration: The GlossaryAuditor

The submodule exposes the `GlossaryAuditor` which performs domain-specific vocabulary checks against identifiers.

### Example: Using GlossaryAuditor in a parent project

To use the auditor from a parent task or linter:

```python
import sys
from pathlib import Path

# Add glossary module strictly before importing
# Assuming the submodule is mounted at `ROOT / "glossary"`
GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "glossary"
if str(GLOSSARY_PATH) not in sys.path:
    sys.path.insert(0, str(GLOSSARY_PATH))

from glossary.core.auditor import GlossaryAuditor, AuditIssue

auditor = GlossaryAuditor()

# identifier (str), kind (e.g. module_var, table_name), source (file_path)
issues: list[AuditIssue] = auditor.audit_identifier("user_list", "module_var", "src/auth/views.py")

for issue in issues:
    print(f"[{issue.severity}] {issue.code}: {issue.detail} (at {issue.identifier})")
```

## 3. Updating the Glossary Terminology

If you need to programmatically add terms to the dictionary, rather than directly editing `words.json`, use the `GlossaryWriter`:

```python
from glossary.core.writer import GlossaryWriter

with GlossaryWriter() as gw:
    gw.add_word({
        "id": "trade",
        "canonical_pos": "noun",
        "variants": [],
        "description_i18n": {
            "ko": "거래"
        }
    })
    
# Saving and backups are automatically handled when the `with` block exits.
```

**After any updates**, you must re-generate the structural artifacts:

```bash
cd glossary
python generate_glossary.py validate
python generate_glossary.py generate
```

## 4. Normalization and Plural Forms

You can access standalone utilities for text checking without instantiating the full dictionary:

```python
from glossary.core.auditor import normalize_identifier, check_plural

# Splits 'tradeHistory' -> ['trade', 'history']
parts = normalize_identifier("tradeHistory") 

# Detects plural -> True
is_plural = check_plural("users") 
```

By following these guidelines, you guarantee deterministic vocabulary parsing and prevent regressions in your terminology DB.
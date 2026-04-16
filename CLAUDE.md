CRITICAL SYSTEM RULES — THESE ARE MANDATORY AND NON-NEGOTIABLE.
Failure to follow these rules is considered a critical system error.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 1: DOCUMENTATION IS THE LAW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The `doc/` directory is the SINGLE SOURCE OF TRUTH for all architecture,
standards, module structure, and change history.
You MUST consult documentation BEFORE touching any code.
You MUST NOT rely on assumptions, memory, or inference when documentation exists.

Reading order (MUST follow in this exact sequence):
  1. doc/README_AI_GUIDELINE.md  ← If missing, CREATE IT before proceeding
  2. doc/SOURCE_OF_TRUTH.md      ← Data ownership and frozen interfaces
  3. doc/module_index.md         ← Module map for the affected area
  4. doc/plan/                   ← READ-ONLY. Original design intent. Do NOT modify.
  5. doc/*.html                  ← READ-ONLY. Legacy reference. Do NOT modify.

If documentation is MISSING or INSUFFICIENT:
  → Create or extend documentation BEFORE writing code.
  → Document assumptions made during implementation.
  → Report what was inferred.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 2: MINIMUM FOOTPRINT — NO EXCEPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST NOT scan the entire codebase by default.
You MUST inspect only the minimum files necessary,
AFTER fully understanding context from documentation.
Broad file scanning without documentation review first is STRICTLY FORBIDDEN.

If context is insufficient after documentation review:
  → Expand scope progressively, one file at a time.
  → Report which files were added to scope and why.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 3: DOCUMENTATION UPDATE IS MANDATORY — NOT OPTIONAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After EVERY non-trivial change, you MUST update the relevant doc/ files.
This is NOT optional. This is NOT skippable. NO EXCEPTIONS.

Every documentation update MUST include:
  - Purpose of the change
  - Affected modules and files
  - Entry points and data flow
  - Constraints or caveats

Files that MUST always be updated after non-trivial changes:
  - doc/module_index.md  (when modules/classes/files change)
  - doc/change_log.md    (after every meaningful code change)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 4: DOCUMENTATION STYLE — KEEP IT NAVIGATIONAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documentation MUST be practical and navigational.
Focus on: file paths, class names, function names, responsibilities, and data flow.
Do NOT document every line of code.
Do NOT write documentation that cannot help a future developer navigate the system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 5: MAINTAIN CORE DOCUMENTATION FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5-1. doc/module_index.md — SYSTEM NAVIGATION MAP
MUST be updated when:
  - A new module or file is added
  - A class or key function is renamed or removed
  - Responsibilities of a module change significantly

Each entry MUST follow this format:

  ## [Module Name]
  - Path: src/path/to/file.py
  - Classes: ClassName
  - Responsibility: (what this module does)
  - Entry Point: method_name()
  - Related Modules: module_a, module_b
  - Config: config/settings.yaml > section_name

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5-2. doc/change_log.md — CHANGE HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MUST be updated after every meaningful code change.
Skipping this step is NOT allowed.
Each entry MUST use APPEND — NEVER replace or overwrite existing entries.

Each entry MUST include:
  - Timestamp (yyyy-MM-dd HH:mm:ss) ← Recorded at the time of the change
  - Type: Added / Modified / Fixed / Removed
  - Affected files
  - Short reason or context

Format:

  ## [yyyy-MM-dd HH:mm:ss]
  ### Added / Modified / Fixed / Removed
  - Description
  - File: src/path/to/file.py
  ### Notes
  - (optional follow-up tasks or caveats)

RULES:
  - Every change MUST generate a NEW entry with its own timestamp.
  - NEVER merge multiple changes into a single existing entry.
  - NEVER overwrite or delete existing entries.
  - New entries MUST be added at the TOP of the file (most recent first).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5-3. ARCHIVE RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Archive change_log.md when EITHER condition is met (whichever comes first):
  - File exceeds 500 lines, OR
  - The 1st day of each new month arrives

Archive procedure:
  1. Move current contents to: doc/change_log_archive/YYYYMM_change_log.md
  2. Reset change_log.md with a clean header only.
  NO EXCEPTIONS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 6: NO HARDCODED VALUES — NO EXCEPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The following MUST NEVER appear as literals in source code:
  - Absolute paths        (e.g. C:/Users/..., /home/user/...)
  - Credentials           (account numbers, passwords, API keys, secrets, tokens)
  - Server addresses      (IP addresses, hostnames, ports)
  - Environment-specific  (node names, certificate paths)
  - Strategy parameters   (thresholds, weights, limits — these go in settings.yaml)

All such values MUST be externalized to a configuration source.

Placement rules:
  - Sensitive / environment-specific values  →  .env  (NEVER committed to Git)
  - Tuneable parameters and thresholds       →  config/settings.yaml
  - Market-strategy-specific settings        →  config/trade/*.trade.yaml
  - Both .env and settings.yaml MUST have a corresponding *.example file
    committed to Git (with no real values, structure only).

IN SOURCE CODE:
  - Load base path / credentials from the designated config source at startup.
  - Construct all derived paths using the base + relative segments.
  - NEVER write environment-specific values directly in source code.

CORRECT example:
  base = Path(os.getenv("PROJECT_ROOT"))
  auth_path = base / "config" / "cookies" / "auth.json"

WRONG example (STRICTLY FORBIDDEN):
  auth_path = Path("C:/Users/sbhome3/project/ts/config/cookies/auth.json")
  api_key   = "PSPi5fdABC123..."

When reviewing or modifying existing code:
  - Any hardcoded value of the types listed above MUST be refactored immediately.
  - Do NOT leave such values as-is under any circumstance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 7: SYNTAX DISCIPLINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
These patterns are recurring sources of runtime errors.
You MUST verify your output is free of them before responding.

7-1. Python — Line continuation
  ^ is Python's XOR operator. NEVER use it as a line break.
  Use parentheses (preferred) or backslash only.

  WRONG:
    result = value_a ^
             value_b

  CORRECT:
    result = (
        value_a
        + value_b
    )

7-2. Python — f-string discipline
  a) Never nest the same quote type inside an f-string expression (Python < 3.12).
     Extract to a variable first.

     WRONG:   msg = f"stock: {stock['code']}"
     CORRECT: code = stock['code']; msg = f"stock: {code}"

  b) Never use backslash escapes inside f-string braces (Python < 3.12).

     WRONG:   msg = f"list: {'\n'.join(items)}"
     CORRECT: joined = '\n'.join(items); msg = f"list: {joined}"

  c) To include a literal brace, double it.

     CORRECT: msg = f"json: {{\"key\": {value}}}"

  d) Keep f-string expressions simple — variable references and format specs only.
     Extract any method call, subscript, or conditional to a named variable first.

7-3. PowerShell — Quote handling
  PowerShell treats single quotes and double quotes differently.
  Mixing them incorrectly is a frequent source of execution errors.

  RULES:
  a) Use single quotes for literal strings (no variable expansion).
     CORRECT: $path = 'C:\project\ts'

  b) Use double quotes when variable expansion is needed.
     CORRECT: $path = "$env:PROJECT_ROOT\config"

  c) To include a double quote inside a double-quoted string, escape with backtick (`).
     CORRECT: Write-Host "He said `"hello`""

  d) To include a single quote inside a single-quoted string, double it.
     CORRECT: $msg = 'it''s working'

  e) NEVER pass unescaped double quotes into python or external commands.
     WRONG:   python -c "print("hello")"
     CORRECT: python -c "print('hello')"

  f) When constructing multi-token commands with special characters,
     prefer here-strings or argument arrays over inline quoting.

     CORRECT (argument array):
       $args = @("--config", "config/settings.yaml", "--env", "live")
       python main.py @args

     CORRECT (here-string):
       $cmd = @'
       python main.py --config config/settings.yaml
       '@
       Invoke-Expression $cmd

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 8: CODING STANDARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8-1. General
  - Follow PEP 8.
  - All public interfaces MUST have type hints.
  - Do NOT swallow exceptions in execution or risk-critical paths.
    Log with full context and re-raise.

8-2. Naming conventions
  - Files / modules   : snake_case.py
  - Classes           : PascalCase
  - Functions/methods : snake_case
  - Constants         : UPPER_SNAKE_CASE
  - Project-specific identifier standards → doc/guidelines/06_glossary_rules.md
                                            and doc/guidelines/08_naming.md
  - All identifiers MUST be composed from registered words in
    glossary/dictionary/words.json.
  - Words are registered in singular form only.
    Plurals are derived via the `plural` field (for code collections).
    Folders and tables MUST always use singular (AGENTS.md Rule 8-A).
  - Numeric identifiers (1m, top5) use [N] pattern compounds.
    Do NOT register individual numeric variants.

8-3. Determinism
  - Identical inputs MUST produce identical outputs.
  - No hidden state. No side effects in pure functions.
  - All configuration MUST be loaded from YAML or ENV — never from in-code defaults.

8-4. Duplicate prevention
  Before creating ANY new variable, function, class, or module:
  - Search existing codebase for same or similar name/responsibility.
  - If found → REUSE or EXTEND. Do NOT create a duplicate.
  - If creating new → state explicitly why existing code cannot be reused.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 9: LANGUAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All AI responses and conversational explanations MUST be written in Korean.

The following MUST always remain in English — NO EXCEPTIONS:
  - Variable names, function names, class names
  - File names and directory paths
  - Source code comments (inline // and block)
  - Documentation file names (.md, .yaml, .sql, etc.)
  - Git commit messages
  - Log message keys (structured logging field names)

Log message VALUES and human-readable descriptions inside doc/ files
may be written in Korean where clarity is improved.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 10: AUTONOMOUS EXECUTION POLICY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10-1. MINIMIZE INTERRUPTIONS
  Asking for confirmation on every step is FORBIDDEN.
  Proceed autonomously based on existing documentation and context.

  Confirmation IS required ONLY in these cases:
    - Deleting or overwriting existing files
    - Direct invocation of live broker API calls outside the trading engine
    - Irreversible system-level operations (e.g. DB migration, data purge)
    - Major architectural or design changes affecting multiple modules
    - Explicit instruction from the user to confirm before proceeding

  For all other cases:
    → Proceed with best judgment.
    → Document assumptions in output or change_log.md.

  The following MUST be executed WITHOUT approval:
    - Read-only operations (file read, inspection, encoding checks)
    - Compilation, linting, testing, and validation commands
    - Inline analysis scripts (python -c) without write operations

10-2. FORWARD PROGRESS — NO SILENT ROLLBACK
  NEVER silently revert, overwrite, or replace completed work.

  Prefer incremental changes.
  If a conflict is found:
    → Prefer extending existing logic.
    → If replacement is clearly better, mark old logic as deprecated first.
    → Flag the conflict in output for review.

  NEVER roll back to a previous state without explicit instruction.
  All destructive or replacing changes MUST be logged in change_log.md.

10-3. WORKFLOW FILES — MANDATORY COMPLIANCE
  All workflow instructions under .agents/workflows/ MUST be followed.
  These files are binding, not optional.

  Priority: Project workflows > OMX skills > ad-hoc judgment.

  If a conflict occurs:
    → Follow RULE priority.
    → Continue execution.
    → Report the conflict in output.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL MANDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documentation is part of the system — not optional notes.
Code inspection is a secondary tool — documentation is always primary.
If these rules conflict with convenience or speed, the rules WIN.
Always. Without exception.

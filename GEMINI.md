CRITICAL SYSTEM RULES — THESE ARE MANDATORY AND NON-NEGOTIABLE.
Failure to follow these rules is considered a critical system error.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 1: DOCUMENTATION IS THE LAW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The `doc/` directory is the SINGLE SOURCE OF TRUTH for all architecture,
standards, module structure, and change history.
You MUST consult documentation BEFORE touching any code.
You MUST NOT rely on assumptions, memory, or inference when documentation exists.

Priority order (MUST follow in this exact sequence):
  1. doc/README_AI_GUIDELINE.md  ← If missing, CREATE IT before proceeding
  2. doc/plan/                   ← READ-ONLY. Reference for original design intent.
                                    Do NOT modify. Do NOT add entries.
  3. doc/*.html                  ← READ-ONLY. Legacy reference documents.
                                    Do NOT modify.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 2: MINIMUM FOOTPRINT — NO EXCEPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST NOT scan the entire codebase by default.
You MUST inspect only the minimum files necessary,
AFTER fully understanding context from documentation.
Broad file scanning without documentation review first is STRICTLY FORBIDDEN.

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
The following files MUST be maintained and updated after every non-trivial change.

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
  - Timestamp (yyyy-MM-dd HH:mi:ss) ← MUST be recorded at the time of the change
  - Type: Added / Modified / Fixed / Removed
  - Affected files
  - Short reason or context

Format:

  ## [yyyy-MM-dd HH:mi:ss]
  ### Added / Modified / Fixed / Removed
  - Description
  - File: src/path/to/file.py
  ### Notes
  - (optional follow-up tasks or caveats)

IMPORTANT:
  - Every change MUST generate a NEW entry with its own timestamp.
  - NEVER merge multiple changes into a single existing entry.
  - NEVER overwrite or delete existing entries.
  - New entries MUST be added at the TOP of the file (most recent first).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5-3. ARCHIVE RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When change_log.md exceeds 500 lines OR on the 7th day of each new month:
  - Move current contents to: doc/change_log_archive/YYYYMM_change_log.md
  - Reset change_log.md with a clean header only
  - NO EXCEPTIONS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 6: NO HARDCODED PATHS — NO EXCEPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hardcoded absolute paths in source code are STRICTLY FORBIDDEN.
All paths MUST be defined in the configuration file and referenced relatively in code.

CONFIGURATION FILE (Single source for all path definitions):
  config/settings.yaml

  paths:
    project_root: "C:/project/ts1"        ← defined ONCE here only
    config_dir: "config"
    cookies_dir: "config/cookies"
    log_dir: "logs"
    data_dir: "data"

IN SOURCE CODE (MUST follow these rules):
  - Load base path from config at startup
  - Construct all file paths using the base path + relative path
  - NEVER write absolute paths directly in source code

CORRECT example:
  base = Path(config["paths"]["project_root"])
  auth_path = base / config["paths"]["cookies_dir"] / "goldenkey_full_auth.json"

WRONG example (STRICTLY FORBIDDEN):
  auth_path = Path("C:/project/ts1/config/cookies/goldenkey_full_auth.json")

When reviewing or modifying existing code:
  - If any hardcoded absolute path is found, it MUST be refactored immediately.
  - Do NOT leave hardcoded paths as-is under any circumstance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 7: LANGUAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All responses and explanations MUST be written in Korean.
However, the following MUST always remain in English:
  - Variable names
  - Function names
  - Class names
  - File names and directory paths
  - Code comments
  - Documentation file names
NO EXCEPTIONS.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL MANDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documentation is part of the system — not optional notes.
Code inspection is a secondary tool — documentation is always primary.
If these rules conflict with convenience or speed, the rules WIN.
Always. Without exception.
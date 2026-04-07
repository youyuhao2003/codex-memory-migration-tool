---
name: codex-memory-migration
description: Recover Codex desktop threads, workspace memory, and project listings after switching APIs, accounts, or model providers. Use when old conversations disappear, projects show "无线程", workspace paths split into different forms like "\\?\\C:\\" vs "C:\\", or local thread metadata needs to be migrated into the current account/provider.
---

# Codex Memory Migration

Use this skill to repair local Codex state after changing API keys, providers, or accounts. It fixes the common Windows failure modes we hit in practice:

- `cwd` path mismatches such as `\\?\C:\...` vs `C:\...`
- threads present on disk but hidden in the UI because `has_user_event` is wrong
- old threads still attached to the previous `model_provider`
- project tree entries not matching the repaired thread paths

## Quick Start

1. Close Codex Desktop completely before changing state on disk.
2. Run `python scripts/codex_memory_migrate.py --dry-run` from this skill folder.
3. Inspect the reported counts and target provider.
4. Run `python scripts/codex_memory_migrate.py --apply --target-provider <current-provider>`.
5. Reopen Codex Desktop.
6. If projects still show `无线程`, read [references/troubleshooting.md](references/troubleshooting.md) and use `--clear-ui-cache`.

## Workflow

### 1. Detect the current provider

Prefer the provider from the newest thread you want to keep using, for example `my_codex`. If the user says "I changed API/account and all old chats are gone", migrate old threads into the provider used by the current account.

### 2. Rebuild thread metadata from session files

Use `scripts/codex_memory_migrate.py` to scan `~/.codex/sessions/**/rollout-*.jsonl` and sync the database with session reality:

- map each thread id to its `rollout_path`
- recover `cwd` from `session_meta`
- mark threads with real user messages as visible
- normalize Windows paths to a single canonical form

### 3. Unify provider ownership

If old threads belong to the previous provider, migrate `threads.model_provider` and the first-line `session_meta.model_provider` in the corresponding `rollout-*.jsonl` files to the current provider.

### 4. Rebuild the project tree

Rebuild `.codex-global-state.json` from visible, non-archived threads so the left sidebar uses the same canonical paths as the repaired threads.

### 5. Clear UI cache only if needed

If the database looks correct but the UI still shows stale project/thread state after a full restart, rerun the script with `--clear-ui-cache`. Only do this with Codex fully closed.

## Commands

Dry run:

```powershell
python scripts/codex_memory_migrate.py --dry-run
```

Apply migration:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex
```

Apply migration and clear Electron thread cache:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex --clear-ui-cache
```

## Safety Rules

- Back up state before writing. The script creates a timestamped backup in `~/.codex/repair_backups/`.
- Refuse to clear UI cache while Codex is still running.
- Treat session files as the source of truth for thread existence, `cwd`, and provider metadata.
- Do not guess the target provider if the user explicitly names one; use the provided value.

## Resources

- `scripts/codex_memory_migrate.py`: Detect and repair local Codex migration issues.
- [references/troubleshooting.md](references/troubleshooting.md): What to check when UI and database still disagree.

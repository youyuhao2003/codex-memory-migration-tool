# Codex Memory Migration

Recover Codex Desktop local threads, workspace memory, and project listings after switching APIs, accounts, or model providers.

This repo packages a Codex skill plus a standalone migration script for the Windows failure modes that commonly appear after changing API endpoints or providers:

- the same workspace stored as both `\\?\C:\...` and `C:\...`
- threads present on disk but hidden in the UI because `has_user_event` is wrong
- old threads still attached to the previous `model_provider`
- sidebar project roots no longer matching the repaired threads
- UI cache still showing `无线程` after the data layer was already fixed

## What It Repairs

- `~/.codex/state_5.sqlite`
- `~/.codex/.codex-global-state.json`
- `~/.codex/sessions/**/rollout-*.jsonl`
- optional Electron local thread cache for Codex Desktop on Windows

## Repository Layout

- `SKILL.md`: Codex skill entrypoint
- `scripts/codex_memory_migrate.py`: standalone migration script
- `references/troubleshooting.md`: troubleshooting guide
- `agents/openai.yaml`: UI metadata for skill discovery

## Use As A Codex Skill

Copy or install this repo into your local Codex skills directory so the skill can be invoked as `$codex-memory-migration`.

Typical local destination on Windows:

```powershell
C:\Users\<you>\.codex\skills\codex-memory-migration
```

## Use As A Standalone Script

Dry run:

```powershell
python scripts/codex_memory_migrate.py --dry-run
```

Apply changes:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex
```

Apply changes and clear Codex Desktop Electron cache:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex --clear-ui-cache
```

## Recommended Workflow

1. Close Codex Desktop completely.
2. Run a dry run first.
3. Identify the provider you want the old threads to belong to, for example `my_codex`.
4. Run the apply command.
5. Reopen Codex Desktop.
6. If the sidebar still shows stale state, rerun with `--clear-ui-cache`.

## Notes

- The script creates timestamped backups in `~/.codex/repair_backups/` before writing.
- The script treats session files as the source of truth for thread existence and user-message visibility.
- On Windows, `--clear-ui-cache` refuses to run while Codex is still open.

## License

MIT

# Troubleshooting

## Symptoms this skill is meant to fix

- Old projects still appear, but every project shows `无线程`
- Current workspace only shows newly created threads
- The same folder appears as both `\\?\C:\...` and `C:\...`
- Threads exist in `~/.codex/sessions`, but the sidebar does not list them
- Old chats belong to the previous `model_provider`

## Checks

### 1. Confirm Codex is fully closed

On Windows, close every `Codex.exe` process before running an apply step that edits caches.

### 2. Run a dry run first

Use:

```powershell
python scripts/codex_memory_migrate.py --dry-run
```

Inspect:

- total thread count
- visible thread count
- provider distribution
- project root count

### 3. Verify provider mismatch

If old threads are mostly under `OpenAI` but the active account uses `my_codex`, migrate providers.

### 4. Verify path mismatch

If one workspace exists in multiple forms, normalize:

- remove `\\?\`
- normalize drive letter casing
- normalize separators to backslashes

### 5. Use cache clearing only after data repair

`--clear-ui-cache` is a UI refresh step, not the primary migration. Use it only after repairing:

- `state_5.sqlite`
- `.codex-global-state.json`
- `rollout-*.jsonl` first-line `session_meta`

## Expected result after a successful run

- `threads.has_user_event` reflects real user messages
- `threads.cwd` matches the project tree path
- `threads.model_provider` matches the current provider
- `.codex-global-state.json` contains canonical workspace roots
- after relaunch, sidebar projects list their threads again

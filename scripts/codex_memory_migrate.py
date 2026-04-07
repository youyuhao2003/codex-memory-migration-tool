import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def canonicalize_path(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return value
    value = value.replace("/", "\\")
    if value.startswith("\\\\?\\"):
        value = value[4:]
    match = re.match(r"^([a-zA-Z]):\\", value)
    if match:
        value = match.group(1).upper() + value[1:]
    return value


def discover_session_files(sessions_root: Path) -> dict[str, dict]:
    sessions: dict[str, dict] = {}
    for path_str in glob.glob(str(sessions_root / "**" / "rollout-*.jsonl"), recursive=True):
        path = Path(path_str)
        thread_id = None
        cwd = None
        provider = None
        saw_user = False
        try:
            with path.open("r", encoding="utf-8") as handle:
                for index, line in enumerate(handle):
                    try:
                        payload = json.loads(line)
                    except Exception:
                        payload = None
                    if payload and payload.get("type") == "session_meta":
                        meta = payload.get("payload", {})
                        thread_id = meta.get("id") or thread_id
                        cwd = canonicalize_path(meta.get("cwd")) or cwd
                        provider = meta.get("model_provider") or provider
                    if '"role":"user"' in line or '"role": "user"' in line:
                        saw_user = True
                    if thread_id and cwd and provider and saw_user and index > 20:
                        break
        except Exception:
            continue
        if thread_id:
            sessions[thread_id] = {
                "path": path,
                "cwd": cwd,
                "provider": provider,
                "has_user_event": saw_user,
            }
    return sessions


def backup_files(home: Path, extra_files: list[Path]) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = home / "repair_backups" / f"codex_memory_migration_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for file_path in extra_files:
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / f"{file_path.name}.bak")
    return backup_dir


def is_codex_running() -> bool:
    if os.name != "nt":
        return False
    try:
        import subprocess

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process | Where-Object { $_.ProcessName -like '*Codex*' } | Select-Object -ExpandProperty Id",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return False
    return bool(result.stdout.strip())


def rewrite_session_meta(session_path: Path, target_cwd: str | None, target_provider: str | None) -> bool:
    try:
        lines = session_path.read_text(encoding="utf-8").splitlines(keepends=True)
        if not lines:
            return False
        first = json.loads(lines[0])
        payload = first.get("payload", {})
        changed = False
        if target_cwd and payload.get("cwd") != target_cwd:
            payload["cwd"] = target_cwd
            changed = True
        if target_provider and payload.get("model_provider") != target_provider:
            payload["model_provider"] = target_provider
            changed = True
        if not changed:
            return False
        first["payload"] = payload
        lines[0] = json.dumps(first, ensure_ascii=False, separators=(",", ":")) + "\n"
        session_path.write_text("".join(lines), encoding="utf-8", newline="")
        return True
    except Exception:
        return False


def rebuild_global_state(global_state_path: Path, visible_roots: list[str]) -> None:
    if not global_state_path.exists():
        return
    state = json.loads(global_state_path.read_text(encoding="utf-8"))
    persisted = state.setdefault("electron-persisted-atom-state", {})
    collapsed = persisted.setdefault("sidebar-collapsed-groups", {})
    canonical_visible = [canonicalize_path(item) for item in visible_roots if item]
    active = [canonicalize_path(item) for item in state.get("active-workspace-roots", []) if item]

    merged: list[str] = []
    seen = set()
    for sequence in (active, state.get("electron-saved-workspace-roots", []), state.get("project-order", []), canonical_visible):
        for item in sequence:
            item = canonicalize_path(item)
            if item and item not in seen:
                merged.append(item)
                seen.add(item)

    state["electron-saved-workspace-roots"] = merged
    state["project-order"] = merged[:]
    state["active-workspace-roots"] = active

    normalized_collapsed = {}
    for key, value in collapsed.items():
        normalized_collapsed[canonicalize_path(key)] = value
    for root in merged:
        normalized_collapsed.setdefault(root, True)
    persisted["sidebar-collapsed-groups"] = normalized_collapsed

    open_pref = state.get("open-in-target-preferences")
    if isinstance(open_pref, dict) and isinstance(open_pref.get("perPath"), dict):
        normalized = {}
        for key, value in open_pref["perPath"].items():
            normalized[canonicalize_path(key)] = value
        open_pref["perPath"] = normalized

    global_state_path.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def clear_ui_cache() -> list[Path]:
    package_root = Path.home() / "AppData" / "Local" / "Packages"
    matches = list(package_root.glob("OpenAI.Codex_*"))
    removed: list[Path] = []
    for root in matches:
        target = root / "LocalCache" / "Roaming" / "Codex" / "Local Storage" / "leveldb"
        if not target.exists():
            continue
        for child in target.iterdir():
            if child.is_file():
                child.unlink()
                removed.append(child)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair local Codex thread/workspace state after API or account switches.")
    parser.add_argument("--apply", action="store_true", help="Write repairs to disk.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing.")
    parser.add_argument("--target-provider", help="Current provider/account key to migrate old threads into, e.g. my_codex.")
    parser.add_argument("--clear-ui-cache", action="store_true", help="Clear Electron local thread cache after data repair. Requires Codex to be closed.")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        parser.error("Specify --dry-run or --apply.")

    home = codex_home()
    db_path = home / "state_5.sqlite"
    global_state_path = home / ".codex-global-state.json"
    session_index_path = home / "session_index.jsonl"
    sessions = discover_session_files(home / "sessions")

    if not db_path.exists():
        print(f"Missing database: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, cwd, rollout_path, model_provider, has_user_event, archived, first_user_message, updated_at FROM threads")
    rows = cur.fetchall()

    provider_counter = Counter(row[3] for row in rows if row[3])
    if args.target_provider:
        target_provider = args.target_provider
    else:
        latest_provider = None
        latest_updated = -1
        for row in rows:
            if row[7] and row[7] > latest_updated and row[3]:
                latest_updated = row[7]
                latest_provider = row[3]
        target_provider = latest_provider or provider_counter.most_common(1)[0][0]

    plan = []
    visible_roots = set()
    provider_changes = 0
    cwd_changes = 0
    rollout_changes = 0
    visible_changes = 0

    for thread_id, cwd, rollout_path, provider, has_user_event, archived, first_user_message, _updated_at in rows:
        session = sessions.get(thread_id)
        target_cwd = canonicalize_path(cwd)
        if session and session.get("cwd"):
            target_cwd = session["cwd"]
        target_visible = 1 if (session and session["has_user_event"]) or (first_user_message or "").strip() else 0
        target_rollout = str(session["path"]) if session else rollout_path
        target_provider_for_thread = target_provider if provider != target_provider else provider

        if target_cwd and not archived and target_visible:
            visible_roots.add(target_cwd)

        changed = (
            canonicalize_path(cwd) != target_cwd
            or rollout_path != target_rollout
            or provider != target_provider_for_thread
            or has_user_event != target_visible
        )
        if changed:
            plan.append((thread_id, target_cwd, target_rollout, target_provider_for_thread, target_visible, session["path"] if session else None))
            provider_changes += int(provider != target_provider_for_thread)
            cwd_changes += int(canonicalize_path(cwd) != target_cwd)
            rollout_changes += int(rollout_path != target_rollout)
            visible_changes += int(has_user_event != target_visible)

    print(f"threads_total={len(rows)}")
    print(f"sessions_found={len(sessions)}")
    print(f"target_provider={target_provider}")
    print(f"planned_threads={len(plan)}")
    print(f"provider_changes={provider_changes}")
    print(f"cwd_changes={cwd_changes}")
    print(f"rollout_changes={rollout_changes}")
    print(f"visible_changes={visible_changes}")
    print(f"project_roots={len(visible_roots)}")

    if args.dry_run and not args.apply:
        return 0

    backup_dir = backup_files(home, [db_path, global_state_path, session_index_path])
    print(f"backup_dir={backup_dir}")

    for thread_id, target_cwd, target_rollout, target_provider_for_thread, target_visible, session_path in plan:
        cur.execute(
            "UPDATE threads SET cwd=?, rollout_path=?, model_provider=?, has_user_event=? WHERE id=?",
            (target_cwd, target_rollout, target_provider_for_thread, target_visible, thread_id),
        )
        if session_path:
            rewrite_session_meta(session_path, target_cwd, target_provider_for_thread)

    conn.commit()
    rebuild_global_state(global_state_path, sorted(visible_roots))

    if args.clear_ui_cache:
        if is_codex_running():
            print("Refusing to clear UI cache while Codex is running.", file=sys.stderr)
            return 2
        removed = clear_ui_cache()
        print(f"ui_cache_files_removed={len(removed)}")

    print("status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

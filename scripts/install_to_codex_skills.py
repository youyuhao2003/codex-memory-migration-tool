import argparse
import os
import shutil
from pathlib import Path


SKILL_NAME = "codex-memory-migration"
INCLUDE_NAMES = {
    "SKILL.md",
    "README.md",
    "LICENSE",
    "PROJECT_INTRO.md",
    "agents",
    "references",
    "scripts",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def codex_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def copy_tree(src: Path, dst: Path) -> None:
    for item in src.iterdir():
        if item.name not in INCLUDE_NAMES:
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install this repository as a local Codex skill.")
    parser.add_argument("--codex-home", help="Override CODEX_HOME. Defaults to $CODEX_HOME or ~/.codex.")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed skill.")
    args = parser.parse_args()

    src_root = repo_root()
    target_root = codex_home(args.codex_home) / "skills" / SKILL_NAME

    if target_root.exists():
        if not args.force:
            print(f"Target already exists: {target_root}")
            print("Re-run with --force to replace it.")
            return 1
        shutil.rmtree(target_root)

    target_root.mkdir(parents=True, exist_ok=True)
    copy_tree(src_root, target_root)

    print(f"Installed skill to: {target_root}")
    print(f"Invoke in Codex as: ${SKILL_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

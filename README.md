# Codex Memory Migration

Recover Codex Desktop local threads, workspace memory, and project listings after switching APIs, accounts, or model providers.

恢复 Codex Desktop 在切换 API、账号或 provider 之后丢失的本地线程、项目树和工作区记忆。

## English

### What this project is

This repository packages:

- a Codex skill: [`SKILL.md`](./SKILL.md)
- a standalone migration tool: [`scripts/codex_memory_migrate.py`](./scripts/codex_memory_migrate.py)
- an installer that copies the skill into `~/.codex/skills`: [`scripts/install_to_codex_skills.py`](./scripts/install_to_codex_skills.py)

It is designed for the common Codex Desktop migration failures that appear after changing API endpoints, custom providers, or logged-in accounts:

- the same workspace stored as both `\\?\C:\...` and `C:\...`
- threads present on disk but hidden in the UI because `has_user_event` is wrong
- old threads still attached to the previous `model_provider`
- sidebar project roots no longer matching repaired thread paths
- Electron UI cache still showing stale `no threads` state

### Is this only for one custom setup?

No. The project is intentionally generic within the Codex Desktop local-state model.

What is generic:

- no hardcoded username, machine name, or provider name
- `CODEX_HOME` is respected when set; otherwise it falls back to `~/.codex`
- provider migration is data-driven and can target any provider string via `--target-provider`
- the script discovers threads from local `rollout-*.jsonl` files instead of relying on one fixed workspace

What is platform-specific:

- the optional `--clear-ui-cache` step is Windows-specific because it clears the Codex Desktop Electron cache under the Windows app package path
- path canonicalization focuses on Windows-style extended paths because that is the most common failure mode this tool targets

### What it repairs

- `~/.codex/state_5.sqlite`
- `~/.codex/.codex-global-state.json`
- `~/.codex/sessions/**/rollout-*.jsonl`
- optional Codex Desktop Electron local thread cache on Windows

### Install as a Codex skill

One-command install:

```powershell
python scripts/install_to_codex_skills.py --force
```

Custom Codex home:

```powershell
python scripts/install_to_codex_skills.py --codex-home "D:\my-codex-home" --force
```

After installation, the skill is available as:

```text
$codex-memory-migration
```

### Use as a standalone tool

Dry run:

```powershell
python scripts/codex_memory_migrate.py --dry-run
```

Apply migration:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex
```

Apply migration and clear Codex Desktop Electron cache:

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex --clear-ui-cache
```

### Recommended workflow

1. Close Codex Desktop completely.
2. Run a dry run first.
3. Decide which provider should own the restored threads.
4. Run the apply command.
5. Reopen Codex Desktop.
6. If the UI is still stale, rerun with `--clear-ui-cache`.

### Repository layout

- [`SKILL.md`](./SKILL.md): Codex skill entrypoint
- [`agents/openai.yaml`](./agents/openai.yaml): Codex UI metadata
- [`scripts/codex_memory_migrate.py`](./scripts/codex_memory_migrate.py): migration logic
- [`scripts/install_to_codex_skills.py`](./scripts/install_to_codex_skills.py): installer
- [`references/troubleshooting.md`](./references/troubleshooting.md): troubleshooting guide
- [`PROJECT_INTRO.md`](./PROJECT_INTRO.md): short bilingual project introduction

## 中文

### 这个项目是什么

这个仓库包含两部分：

- 一个可直接给 Codex 使用的 skill：[`SKILL.md`](./SKILL.md)
- 一个可单独运行的迁移脚本：[`scripts/codex_memory_migrate.py`](./scripts/codex_memory_migrate.py)
- 一个可一键安装到 `~/.codex/skills` 的安装器：[`scripts/install_to_codex_skills.py`](./scripts/install_to_codex_skills.py)

它主要解决 Codex Desktop 在切换 API、切换 provider、切换账号之后常见的本地状态错乱问题，比如：

- 同一个工作区同时被记成 `\\?\C:\...` 和 `C:\...`
- 线程文件还在，但侧边栏因为 `has_user_event` 异常而显示不出来
- 老线程仍然挂在旧的 `model_provider` 上
- 左侧项目树路径和线程里的 `cwd` 不一致
- 数据层已经修好，但 Electron 缓存还在显示“无线程”

### 它是不是只适合我的定制环境

不是。这套工具不是按你的用户名、你的 API、你的机器路径写死的，而是按 Codex Desktop 的本地数据结构做的通用迁移。

通用部分：

- 没有写死用户名、电脑名、固定 provider
- 优先读取 `CODEX_HOME`，没有时才回落到 `~/.codex`
- `--target-provider` 可以迁到任意 provider 名称
- 线程是从本地 `rollout-*.jsonl` 自动发现的，不依赖某一个固定项目

平台相关部分：

- `--clear-ui-cache` 目前是 Windows 专用，因为它清理的是 Windows 下 Codex Desktop 的 Electron 缓存目录
- 路径规范化重点处理的是 Windows 扩展路径问题，因为这正是最常见的迁移故障来源

### 它会修什么

- `~/.codex/state_5.sqlite`
- `~/.codex/.codex-global-state.json`
- `~/.codex/sessions/**/rollout-*.jsonl`
- Windows 下可选的 Codex Desktop UI 缓存

### 一键安装到 `~/.codex/skills`

直接执行：

```powershell
python scripts/install_to_codex_skills.py --force
```

如果你的 Codex home 不在默认位置：

```powershell
python scripts/install_to_codex_skills.py --codex-home "D:\my-codex-home" --force
```

安装完成后，你可以直接这样触发：

```text
$codex-memory-migration
```

### 作为独立脚本使用

先 dry-run：

```powershell
python scripts/codex_memory_migrate.py --dry-run
```

正式应用迁移：

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex
```

如果界面缓存没刷新，再加：

```powershell
python scripts/codex_memory_migrate.py --apply --target-provider my_codex --clear-ui-cache
```

### 推荐使用流程

1. 彻底关闭 Codex Desktop。
2. 先执行 dry-run。
3. 确定你想让老线程归属到哪个 provider。
4. 运行 apply。
5. 重开 Codex Desktop。
6. 如果界面仍然显示旧状态，再加 `--clear-ui-cache`。

## License

MIT

# Project Intro

## English

Codex Memory Migration is a small recovery toolkit for Codex Desktop users who switch APIs, model providers, or accounts and suddenly lose visible thread history in the UI.

Instead of relying on one custom provider setup, it works from Codex's local state layout:

- it rebuilds thread visibility from session files
- normalizes broken workspace path variants
- migrates old threads to a new provider identity
- rebuilds the project tree index
- optionally clears stale Electron UI cache on Windows

The goal is simple: when the local data still exists, recover it into the currently active Codex workspace view.

## 中文

Codex Memory Migration 是一个面向 Codex Desktop 的本地恢复工具。它解决的是用户在切换 API、切换 provider、切换账号之后，明明本地会话数据还在，但界面里线程和项目记忆却“消失了”的问题。

它不是围绕某个私有 API 定制的，而是围绕 Codex 的本地状态结构工作的：

- 从 session 文件反推线程可见性
- 统一错误分裂的工作区路径
- 把老线程迁移到新的 provider 身份
- 重建项目树索引
- 在 Windows 上按需清理过期的 Electron 缓存

目标很直接：只要本地数据还在，就尽量把它恢复到当前正在使用的 Codex 工作区视图里。

---
name: token-tracker
description: 查看 Claude Code / Codex token 历史用量报告。当用户询问 token 消耗、费用统计、每日/每周/每月用量、历史会话记录时使用。触发词：tt daily、看一下 token 用量、今天用了多少、费用统计、历史会话。
---

# token-tracker — token 历史用量报告

`tt` 是独立 CLI 工具（pip 包 `token-tracker`），读取 Claude Code / Codex 的本地日志生成统计报告。与 `tt-statusline`（实时状态栏）配合使用，前者看历史，后者看当前。

## 常用命令

```bash
tt daily        # 按日汇总（token 量、费用、会话数、消息数）
tt weekly       # 按周汇总
tt monthly      # 按月汇总
tt sessions     # 最近会话列表（含项目名、token、费用、消息数）
tt dashboard    # 实时仪表盘
tt claude       # 仅 Claude Code 统计
tt codex        # 仅 Codex 统计
tt --version    # 查看版本
```

## 安装

```bash
pip install token-tracker
```

安装后执行 `tt setup` 完成与 Claude Code 的集成配置。

## 与 tt-statusline 的关系

| | token-tracker (`tt`) | tt-statusline |
|--|---------------------|---------------|
| 作用 | 历史用量报告 | 实时状态栏 |
| 触发 | 手动执行命令 | 每次 LLM 调用后自动刷新 |
| 数据 | 本地日志聚合 | 当前会话 JSON |

> `tt setup` 会将 `tt-statusline.py` 写入 `~/.claude/`。若本地已有自定义版本，需注意版本号保持为 `"1.5"` 以防被覆盖，详见 [[tt-statusline]] `references/config.md`。

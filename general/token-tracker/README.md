# token-tracker

> Claude Code / Codex token 历史用量报告工具。

## 安装

```bash
pip install token-tracker
tt setup   # 与 Claude Code 集成
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `tt daily` | 按日汇总 token、费用、会话数 |
| `tt weekly` | 按周汇总 |
| `tt monthly` | 按月汇总 |
| `tt sessions` | 最近会话列表 |
| `tt dashboard` | 实时仪表盘 |
| `tt claude` | 仅 Claude Code 统计 |
| `tt codex` | 仅 Codex 统计 |

## 注意事项

`tt setup` 会向 `~/.claude/` 写入 `tt-statusline.py`。若已安装自定义 `tt-statusline`，需保持脚本 `__version__ = "1.5"` 以防被覆盖。

详见 [tt-statusline](../tt-statusline/)。

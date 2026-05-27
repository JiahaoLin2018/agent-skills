# tt 命令参考

当前版本：0.3.5

## 所有子命令

| 命令 | 说明 |
|------|------|
| `tt dashboard` | 实时仪表盘 |
| `tt daily` | 按日汇总（token、费用、会话数、消息数），按消耗量倒序排列 |
| `tt weekly` | 按周汇总 |
| `tt monthly` | 按月汇总 |
| `tt sessions` | 最近 20 条会话（项目名、token、费用、消息数） |
| `tt claude` | 仅统计 Claude Code 数据 |
| `tt codex` | 仅统计 Codex 数据 |
| `tt setup` | 安装与 Claude Code 的集成配置（写入 tt-statusline.py） |
| `tt unsetup` | 卸载集成配置 |
| `tt --version` | 显示版本号 |

## 输出示例

### tt daily

```
Token Tracker  ● Claude Code
Overview  Token: 2.99B  Cost: $2216  Sessions: 295  Messages: 14378  Days: 37

  Date                       Tokens          Cost          Sessions      Msgs
 ─────────────────────────────────────────────────────────────────────────────
  2026-05-13                 635.0M          $380                22      1604
  2026-05-18                 323.7M          $276                12       962
```

### tt sessions

```
Token Tracker  Recent 20 / 256 sessions  Token: 85.3M  Cost: $71.06

  Time          Project          Tokens     Cost   Msgs
 ───────────────────────────────────────────────────────
  05-21 07:39   agent-skills     469.4K   $0.316     14
  05-21 05:58   iron-flow-scf      7.1M    $8.29     55
```

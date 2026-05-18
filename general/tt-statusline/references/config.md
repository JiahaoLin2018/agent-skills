# tt-statusline 状态栏说明

## 示例效果

```
[Sonnet 4.6 | Max] │ ◑ 27% │ S×3 54k │ [jiahao]
5h ██░░░░░░ 28% (2h0m · 12:00) │ 7d ░░░░░░░░ 2% (4d22h · 05/23 08:00)
上轮 S×2 102 │ 本轮 S×1 105 │ Cached 53k │ $6.59 │ 2d16h
```

---

## 第 1 行 — 会话概览

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `[Sonnet 4.6 \| Max]` | 当前模型 + 思考模式（Max/High/Normal） | `model.display_name` + `effort.level` |
| `◑ 27%` | 上下文窗口占用率，绿 < 50%，黄 < 80%，红 ≥ 80% | `context_window.used_percentage` |
| `S×3` | 本次会话累计 LLM 交互次数（每次 Stop 事件 +1） | `tt-round-state.json → session_total` |
| `54k` | 本次会话累计 input tokens 总量 | `context_window.total_input_tokens` |
| `[jiahao]` | 当前项目目录名 | `workspace.project_dir` basename |

---

## 第 2 行 — 速率限制

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `5h ██░░ 28%` | 5 小时窗口额度进度条 + 百分比 | `rate_limits.five_hour.used_percentage` |
| `(2h0m · 12:00)` | 距重置剩余时间 + 重置时刻（跨天显示 mm/dd HH:MM） | `rate_limits.five_hour.resets_at` |
| `7d ░░░░ 2%` | 7 天窗口额度进度条 + 百分比 | `rate_limits.seven_day.used_percentage` |
| `(4d22h · 05/23 08:00)` | 距重置剩余时间 + 重置时刻 | `rate_limits.seven_day.resets_at` |

---

## 第 3 行 — 轮次对比

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `上轮 S×2 102` | 上一轮：LLM 交互次数 + 那一轮新增 input tokens | `tt-round-state.json → prev / prev_round_tokens` |
| `本轮 S×1 105` | 当前轮：LLM 交互次数 + 本轮新增 input tokens | `tt-round-state.json → current / curr_round_tokens` |
| `Cached 53k` | 当前调用命中 prompt cache 的 tokens 数 | `context_window.current_usage.cache_read_input_tokens` |
| `$6.59` | 本次会话累计费用（USD） | `cost.total_cost_usd` |
| `2d16h` | 本次会话已运行时长 | `cost.total_duration_ms` |

> **"轮"的定义**：用户发送一条消息 → Claude 完成所有响应（含工具调用）为止算一轮。
> 轮次检测：读取 transcript JSONL 中 `last-prompt` 条目数变化来判断。

---

## 颜色方案

| 颜色 | ANSI | 用途 |
|------|------|------|
| 青色 | 38;5;117 | 模型名称 |
| 绿色 | 38;5;114 | 项目名 / 上下文使用率<50% / 轮次标签 |
| 黄色 | 38;5;221 | 使用率 50–80% |
| 红色 | 38;5;204 | 使用率 ≥80% |
| 蓝色 | 38;5;111 | 速率限制标签（5h / 7d） |
| 橙色 | 38;5;216 | Token 数量 |
| 洋红 | 38;5;213 | 费用 |
| 灰色 | 38;5;244 | 时长 / 无数据占位符 |

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `~/.claude/tt-statusline.py` | 主脚本，从 stdin 读取 JSON，输出 ANSI 状态栏 |
| `~/.claude/tt-round-state.json` | 轮次状态持久化（session_id / current / prev / last_prompt_count 等） |
| `~/.claude/tt-status.json` | 最近一次 Stop 事件的原始数据快照 |
| `~/.claude/settings.json` | statusLine 命令配置 + UserPromptSubmit hook 配置 |
| `~/.claude/hooks/on-prompt-submit.sh` | 用户提问时写入 flag 文件，辅助轮次检测 |

---

## 实现要点

1. **触发机制**：Claude Code 每次 LLM 调用结束（Stop 事件）时，将会话 JSON 通过 stdin 传给 `tt-statusline.py`，脚本输出的文本显示为状态栏。

2. **轮次检测双保险**：
   - 方法 1：`on-prompt-submit.sh` hook 在用户提问时写入 `tt-new-round.flag`
   - 方法 2：读取 transcript JSONL 中 `last-prompt` 条目数，增加则判定为新轮
   - 两种方式都必须在同一处更新 `last_prompt_count`，否则会导致重复触发

3. **token 累计规则**：`total_input_tokens` 是本次会话累计值（可用）；`total_output_tokens` 只是当前调用的值（非累计），不用于轮次 delta 计算。

4. **Windows 编码**：脚本开头 `sys.stdout.reconfigure(encoding="utf-8")` 处理 Windows GBK 默认编码问题。

5. **状态文件写入**：使用 `tempfile.mkstemp` + `os.replace` 原子写入，避免并发读写损坏。

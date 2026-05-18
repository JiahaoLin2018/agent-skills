# tt-statusline 状态栏说明

## 示例效果

```
Opus 4.7 (1M context) Max │ ◔33% 334k │ S×2 🔧172 │ 📁jiahao
5h █████░░░ 63% ✅ 够用 (1h46m · 17:00) │ 7d █░░░░░░░ 12% (4d16h · 05/23 08:00)
⏮️ S×0 -- │ ⏯️ S×2 5k │ ⚡329k 99% │ $11.92 3.6/h │ 3h17m
```

---

## 第 1 行 — 会话概览

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `Opus 4.7 (1M context) Max` | 模型名 + 思考模式（Max/High/Normal） | `model.display_name` + `effort.level` |
| `◔33%` | 上下文窗口占用率。圆形图标随百分比变化：○<25% ◔<50% ◑<75% ◕<90% ●≥90%；颜色绿<50% 黄<80% 红≥80% | `context_window.used_percentage` |
| `334k` | 当前上下文实际占用 token | `current_usage` 的 input + cache_creation + cache_read 求和 |
| `S×2` | 会话累计 LLM 调用次数 | `tt-round-state.json → session_total` |
| `🔧172` | 会话累计工具调用次数 | transcript 中 `tool_use` 出现次数 |
| `📁jiahao` | 当前项目目录名 | `workspace.project_dir` basename |

---

## 第 2 行 — 速率限制

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `5h █████░░░ 63%` | 5 小时窗口额度进度条 + 百分比 | `rate_limits.five_hour.used_percentage` |
| `✅ 够用` / `⚠ 2h` | 燃尽预测：按消耗速率推算 5h 额度够不够用到重置。够用为绿色，会提前耗尽则红色 `⚠`+预计剩余时间 | 派生：used% ÷ 已用窗口时间 |
| `(1h46m · 17:00)` | 距重置倒计时 · 重置时刻（跨天显示 `MM/DD HH:MM`） | `rate_limits.five_hour.resets_at` |
| `7d █░░░░░░░ 12%` | 7 天窗口额度进度条 + 百分比 | `rate_limits.seven_day.used_percentage` |
| `(4d16h · 05/23 08:00)` | 距重置倒计时 · 重置时刻 | `rate_limits.seven_day.resets_at` |

---

## 第 3 行 — 轮次 / 缓存 / 成本

| 字段 | 说明 | 数据来源 |
|------|------|---------|
| `⏮️ S×0 --` | 上一轮：LLM 调用次数 + 那一轮新增 input token（无数据显示 `--`） | `tt-round-state.json → prev` |
| `⏯️ S×2 5k` | 当前轮：LLM 调用次数 + 本轮新增 input token | `tt-round-state.json → current` |
| `⚡329k 99%` | 缓存命中：命中的 token 量 + 命中率 | `current_usage.cache_read_input_tokens` |
| `$11.92 3.6/h` | 会话累计费用 + 消耗速率（美元/小时） | `cost.total_cost_usd` ÷ 会话小时数 |
| `3h17m` | 会话已运行时长 | `cost.total_duration_ms` |

> **"轮"的定义**：用户发送一条消息 → Claude 完成所有响应（含工具调用）为止算一轮。
> 轮次检测：读取 transcript JSONL 中 `last-prompt` 条目数变化来判断。

---

## 图标含义

| 图标 | 含义 |
|------|------|
| `○ ◔ ◑ ◕ ●` | 上下文占用率（随百分比变化的圆形进度） |
| `🔧` | 工具调用次数 |
| `⏮️` / `⏯️` | 上一轮 / 当前轮 |
| `⚡` | 缓存命中 |
| `📁` | 项目目录 |
| `✅` / `⚠` | 5h 额度够用 / 燃尽预警 |

---

## 颜色方案

| 颜色 | ANSI | 用途 |
|------|------|------|
| 青色 | 38;5;117 | 模型名称 / 缓存命中 |
| 绿色 | 38;5;114 | 上下文使用率<50% / 调用计数 / 轮次 / ✅够用 |
| 黄色 | 38;5;221 | 使用率 50–80% |
| 红色 | 38;5;204 | 使用率 ≥80% / ⚠ 燃尽预警 |
| 蓝色 | 38;5;111 | 速率限制标签（5h / 7d） |
| 橙色 | 38;5;216 | 轮次 token |
| 洋红 | 38;5;213 | 费用 |
| 灰色 | 38;5;244 | 时长 / 倒计时与重置时刻 / 派生指标 / 占位符 |

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

3. **token 字段说明**：`total_input_tokens` 并非会话累计值——实测它精确等于当前上下文输入（`current_usage` 输入侧求和）；`total_output_tokens` 同理只是单次调用值。脚本不依赖二者做累计统计。

4. **transcript 单次扫描**：`scan_transcript` 一次遍历同时统计 `last-prompt`（轮次）和 `tool_use`（工具调用次数），避免重复读取大文件。

5. **派生指标**：燃尽预测、缓存命中率、消耗速率均由现有字段实时计算，不额外存储。燃尽预测在 5h 窗口刚重置（已用时间不足 10 分钟，速率不稳）或 `used%=0` 时不显示。

6. **Windows 编码**：脚本开头 `sys.stdout.reconfigure(encoding="utf-8")` 处理 Windows GBK 默认编码问题。

7. **状态文件写入**：使用 `tempfile.mkstemp` + `os.replace` 原子写入，避免并发读写损坏。

8. **规避 token-tracker 覆盖**：脚本 `__version__` 固定为 `"1.5"`。token-tracker 的 `tt` 命令（如 `tt daily`）运行前会检查 `~/.claude/tt-statusline.py` 的 `__version__`，与其内置 `HOOK_VERSION` 不一致就用自带脚本覆盖本文件。保持 `"1.5"` 即可避免；该字段仅为标记，脚本逻辑不读取。

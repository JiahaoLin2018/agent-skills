#!/usr/bin/env python3
"""Claude Code statusLine — token tracker 状态栏（自定义版，实际 v2.6）"""
# __version__ 必须固定为 "1.5"：token-tracker 的 needs_update() 读此字段，
# 与其内置 HOOK_VERSION("1.5") 不一致时会用自带脚本覆盖本文件（tt daily 等命令触发）。
__version__ = "1.5"
import json, os, re, sys, tempfile
from datetime import datetime, timezone

STATUS_FILE      = os.path.expanduser("~/.claude/tt-status.json")
ROUND_STATE_FILE = os.path.expanduser("~/.claude/tt-round-state.json")
NEW_ROUND_FLAG   = os.path.expanduser("~/.claude/tt-new-round.flag")

ANSI_RE = re.compile(r'\033\[[0-9;]*m')
SEP = " │ "

C = {
    "green":   "\033[38;5;114m",
    "yellow":  "\033[38;5;221m",
    "red":     "\033[38;5;204m",
    "cyan":    "\033[38;5;117m",
    "blue":    "\033[38;5;111m",
    "magenta": "\033[38;5;213m",
    "peach":   "\033[38;5;216m",
    "dim":     "\033[38;5;244m",
    "reset":   "\033[0m",
}

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def vlen(s):
    return len(ANSI_RE.sub("", s))


def get_width():
    try:
        return max(1, os.get_terminal_size(2).columns - 4)
    except Exception:
        return 116


def color_by_pct(pct):
    return C["green"] if pct < 50 else C["yellow"] if pct < 80 else C["red"]


def fmt_tokens(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}k"
    return str(n)


def progress_bar(pct, bar_width=8):
    filled = round(max(0.0, min(100.0, float(pct))) / 100 * bar_width)
    col = color_by_pct(pct)
    return f"{col}{'█' * filled}{C['reset']}{'░' * (bar_width - filled)} {pct:.0f}%"


def fmt_duration(seconds):
    if seconds >= 86400:
        d, rem = int(seconds // 86400), int(seconds % 86400)
        return f"{d}d{rem // 3600}h"
    if seconds >= 3600:
        h, m = int(seconds // 3600), int((seconds % 3600) // 60)
        return f"{h}h{m}m"
    if seconds >= 60:
        return f"{int(seconds // 60)}min"
    return f"{int(seconds)}s"


def fmt_reset(resets_at, now_ts):
    """倒计时 · 重置时刻：当天显示 HH:MM，跨天显示 MM/DD HH:MM。"""
    remain = int(resets_at) - now_ts
    if remain <= 0:
        return ""
    dt = datetime.fromtimestamp(int(resets_at))
    clock = dt.strftime("%H:%M") if remain < 86400 else dt.strftime("%m/%d %H:%M")
    return f"{fmt_duration(remain)} · {clock}"


def burn_forecast(entry, now_ts, window_sec):
    """限额燃尽预测：按已消耗速率推算是否会在重置前耗尽。
    返回 (文案, 颜色)；窗口刚开始或数据不足时返回 None。"""
    pct       = entry.get("used_percentage")
    resets_at = entry.get("resets_at")
    if not pct or not resets_at:
        return None
    remain = int(resets_at) - now_ts          # 距重置剩余秒数
    if remain <= 0:
        return None
    elapsed = window_sec - remain             # 窗口已用秒数
    if elapsed < 600:                         # 不足 10min，速率不稳，不预测
        return None
    rate = pct / elapsed                      # 每秒消耗的百分比
    exhaust_in = (100 - pct) / rate           # 预计耗尽还需秒数
    if exhaust_in >= remain:
        return ("✅ 够用", C["green"])
    return (f"⚠ {fmt_duration(exhaust_in)}", C["red"])


def scan_transcript(transcript_path):
    """扫描 transcript：返回 (用户提问轮次, 工具调用次数)。
    轮次 = last-prompt 条目数；工具调用 = tool_use 出现次数。"""
    prompts = tools = 0
    if not transcript_path or not os.path.exists(transcript_path):
        return prompts, tools
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"last-prompt"' in line:
                    prompts += 1
                tools += line.count('"type":"tool_use"')
    except Exception:
        pass
    return prompts, tools


def update_round_state(session_id, total_in, prompt_count):
    """
    用 transcript last-prompt 计数检测新轮，维护轮次状态。
    prompt_count 由调用方传入（transcript 中 last-prompt 条目数）。
    返回 (prev_stops, curr_stops, session_total, prev_round_tokens, curr_round_tokens)
      - session_total    : 本次会话累计 LLM 调用次数
      - prev/curr_stops  : 上/本轮 LLM 调用次数
      - prev_round_tokens: 上轮 input token 增量
      - curr_round_tokens: 本轮 input token 增量（至今）
    """
    try:
        with open(ROUND_STATE_FILE) as f:
            state = json.load(f)
    except Exception:
        state = {}

    # 检测新轮：方法1 flag 文件，方法2 transcript last-prompt 计数增加
    new_round = False

    try:
        with open(NEW_ROUND_FLAG) as f:
            flagged = f.read().strip()
        if flagged == session_id:
            os.unlink(NEW_ROUND_FLAG)
            new_round = True
    except Exception:
        pass

    if not new_round and prompt_count > state.get("last_prompt_count", 0):
        new_round = True

    if prompt_count > 0:
        state["last_prompt_count"] = prompt_count

    if state.get("session_id") != session_id:
        state = {
            "session_id":        session_id,
            "current":           1,
            "prev":              0,
            "session_total":     1,
            "last_prompt_count": prompt_count,
            "round_start_input": total_in,
            "prev_round_tokens": 0,
        }
    elif new_round:
        curr_delta = max(0, total_in - state.get("round_start_input", total_in))
        state["prev"]              = state.get("current", 0)
        state["prev_round_tokens"] = curr_delta
        state["round_start_input"] = total_in
        state["current"]           = 1
        state["session_total"]     = state.get("session_total", 0) + 1
    else:
        state["current"]       = state.get("current", 0) + 1
        state["session_total"] = state.get("session_total", 0) + 1

    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ROUND_STATE_FILE), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(state, f)
        os.replace(tmp, ROUND_STATE_FILE)
    except Exception:
        pass

    curr_round_tokens = max(0, total_in - state.get("round_start_input", total_in))
    return (
        state.get("prev", 0),
        state.get("current", 1),
        state.get("session_total", 1),
        state.get("prev_round_tokens", 0),
        curr_round_tokens,
    )


def save_data(data, now):
    data["_received_at"] = now.isoformat()
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STATUS_FILE), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp, STATUS_FILE)
    except OSError:
        if tmp:
            try: os.unlink(tmp)
            except OSError: pass


def render(data, now):
    W      = get_width()
    ctx    = data.get("context_window") or {}
    cost   = data.get("cost") or {}
    rl     = data.get("rate_limits") or {}
    bar_w  = 8 if W >= 100 else 6 if W >= 60 else 4
    now_ts = int(now.timestamp())

    total_in = ctx.get("total_input_tokens") or 0
    curr     = ctx.get("current_usage") or {}
    turn_in  = (curr.get("input_tokens") or 0) + (curr.get("cache_creation_input_tokens") or 0)

    session_id      = data.get("session_id", "")
    transcript_path = data.get("transcript_path", "")
    prompt_count, tool_count = scan_transcript(transcript_path)

    prev_stops, curr_stops, session_total, prev_round_tokens, curr_round_tokens = \
        update_round_state(session_id, total_in, prompt_count)

    # ── Line 1: Model Effort │ ◔CTX% Tokens │ S×N 🔧N │ 📁Project ──
    line1 = []

    model_name = (data.get("model") or {}).get("display_name", "")
    effort     = (data.get("effort") or {}).get("level", "")
    if model_name:
        label = f"{model_name} {effort.capitalize()}" if effort else model_name
        line1.append(f"{C['cyan']}{label}{C['reset']}")

    ctx_pct = ctx.get("used_percentage")
    if ctx_pct is not None:
        circle = "○" if ctx_pct < 25 else "◔" if ctx_pct < 50 else "◑" if ctx_pct < 75 else "◕" if ctx_pct < 90 else "●"
        seg = f"{color_by_pct(ctx_pct)}{circle}{ctx_pct:.0f}%{C['reset']}"
        # 当前上下文实际占用 token = 本次请求输入侧总量（非缓存输入 + 缓存写入 + 缓存读取）
        ctx_tokens = ((curr.get("input_tokens") or 0)
                      + (curr.get("cache_creation_input_tokens") or 0)
                      + (curr.get("cache_read_input_tokens") or 0))
        if ctx_tokens > 0:
            seg += f" {C['dim']}{fmt_tokens(ctx_tokens)}{C['reset']}"
        line1.append(seg)

    # S×N = 会话累计 LLM 调用次数；🔧N = 会话累计工具调用次数
    line1.append(f"{C['green']}S×{session_total} 🔧{tool_count}{C['reset']}")

    cwd = (data.get("workspace") or {}).get("current_dir", "")
    if cwd:
        line1.append(f"{C['green']}📁 {os.path.basename(cwd)}{C['reset']}")

    # ── Line 2: 5h bar 燃尽预测 重置时刻 │ 7d bar 重置日期 ──
    line2 = []
    window = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}
    for key, label in [("five_hour", "5h"), ("seven_day", "7d")]:
        entry = rl.get(key) or {}
        pct   = entry.get("used_percentage")
        if pct is None:
            continue
        seg = f"{C['blue']}{label}{C['reset']} {progress_bar(pct, bar_w)}"
        # 燃尽预测仅 5h 显示（7d 周期长，预测意义小）
        if key == "five_hour":
            fc = burn_forecast(entry, now_ts, window[key])
            if fc:
                seg += f" {fc[1]}{fc[0]}{C['reset']}"
        resets_at = entry.get("resets_at")
        if resets_at:
            t = fmt_reset(resets_at, now_ts)
            if t:
                seg += f" {C['dim']}({t}){C['reset']}"
        line2.append(seg)

    # ── Line 3: ⏮上轮 │ ⏯本轮 │ ⚡缓存 命中率 │ $费用 速率 │ 时长 ──
    line3 = []

    prev_tok = fmt_tokens(prev_round_tokens) if prev_round_tokens > 0 else f"{C['dim']}--{C['reset']}"
    line3.append(f"{C['green']}⏮️ S×{prev_stops}{C['reset']} {C['peach']}{prev_tok}{C['reset']}")

    curr_tok = fmt_tokens(curr_round_tokens) if curr_round_tokens > 0 else fmt_tokens(turn_in)
    line3.append(f"{C['green']}⏯️ S×{curr_stops}{C['reset']} {C['peach']}{curr_tok}{C['reset']}")

    # ⚡ 缓存命中：cache_read 量 + 命中率（cache_read 占输入侧总量比例）
    cache_read = curr.get("cache_read_input_tokens") or 0
    ctx_in     = ((curr.get("input_tokens") or 0)
                  + (curr.get("cache_creation_input_tokens") or 0)
                  + cache_read)
    if cache_read > 0:
        seg = f"{C['cyan']}⚡{fmt_tokens(cache_read)}{C['reset']}"
        if ctx_in > 0:
            seg += f" {C['dim']}{cache_read / ctx_in * 100:.0f}%{C['reset']}"
        line3.append(seg)

    # $ 费用 + 消耗速率（$/小时）
    usd         = cost.get("total_cost_usd")
    duration_ms = cost.get("total_duration_ms")
    if usd is not None:
        seg = f"{C['magenta']}${usd:.2f}{C['reset']}"
        if duration_ms and duration_ms > 0:
            hours = duration_ms / 3_600_000
            if hours > 0:
                seg += f" {C['dim']}{usd / hours:.1f}/h{C['reset']}"
        line3.append(seg)

    if duration_ms and duration_ms > 0:
        line3.append(f"{C['dim']}{fmt_duration(duration_ms / 1000)}{C['reset']}")

    output = [SEP.join(line) for line in (line1, line2, line3) if line]
    if output:
        print("\n".join(output))
        sys.stdout.flush()


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    now = datetime.now(timezone.utc)
    save_data(data, now)
    render(data, now)


if __name__ == "__main__":
    main()

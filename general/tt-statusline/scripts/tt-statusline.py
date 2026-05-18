#!/usr/bin/env python3
"""Claude Code statusLine — token tracker 状态栏"""
__version__ = "2.4"
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
    remain = int(resets_at) - now_ts
    if remain <= 0:
        return ""
    dt = datetime.fromtimestamp(int(resets_at))
    clock = dt.strftime("%H:%M") if remain < 86400 else dt.strftime("%m/%d %H:%M")
    return f"{fmt_duration(remain)} · {clock}"


def count_last_prompts(transcript_path):
    """统计 transcript 中 last-prompt 条目数作为用户提问轮次。"""
    if not transcript_path or not os.path.exists(transcript_path):
        return 0
    count = 0
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"last-prompt"' in line:
                    count += 1
    except Exception:
        pass
    return count


def update_round_state(session_id, total_in, transcript_path):
    """
    用 transcript last-prompt 计数检测新轮，维护状态。
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
    # 必须在最前面获取，无论哪种方式触发都要同步更新，避免下一次 Stop 重复误判
    new_round = False
    prompt_count = count_last_prompts(transcript_path)

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

    total_in  = ctx.get("total_input_tokens")  or 0
    total_out = ctx.get("total_output_tokens") or 0
    total     = total_in + total_out

    curr    = ctx.get("current_usage") or {}
    turn_in = (curr.get("input_tokens") or 0) + (curr.get("cache_creation_input_tokens") or 0)

    session_id      = data.get("session_id", "")
    transcript_path = data.get("transcript_path", "")

    prev_stops, curr_stops, session_total, prev_round_tokens, curr_round_tokens = \
        update_round_state(session_id, total_in, transcript_path)

    # ── Line 1: [Model | Effort] │ ◑ CTX% │ S×N Total │ [Project] ──
    line1 = []

    model_name = (data.get("model") or {}).get("display_name", "")
    effort     = (data.get("effort") or {}).get("level", "")
    if model_name:
        inner = f"{model_name} | {effort.capitalize()}" if effort else model_name
        line1.append(f"{C['cyan']}[{inner}]{C['reset']}")

    ctx_pct = ctx.get("used_percentage")
    if ctx_pct is not None:
        circle = "○" if ctx_pct < 20 else "◔" if ctx_pct < 40 else "◑" if ctx_pct < 60 else "◕" if ctx_pct < 80 else "●"
        line1.append(f"{color_by_pct(ctx_pct)}{circle} {ctx_pct:.0f}%{C['reset']}")

    # S×N = 本次会话累计 LLM 调用次数
    parts = [f"S×{session_total}"]
    if total > 0:
        parts.append(fmt_tokens(total))
    line1.append(f"{C['green']}{' '.join(parts)}{C['reset']}")

    project = (data.get("workspace") or {}).get("project_dir", "")
    if project:
        line1.append(f"{C['green']}[{os.path.basename(project)}]{C['reset']}")

    # ── Line 2: 5h / 7d rate limits + 倒计时 · 重置时间 ──
    line2 = []
    for key, label in [("five_hour", "5h"), ("seven_day", "7d")]:
        entry = rl.get(key) or {}
        pct   = entry.get("used_percentage")
        if pct is None:
            continue
        bar = progress_bar(pct, bar_w)
        reset_str = ""
        resets_at = entry.get("resets_at")
        if resets_at:
            t = fmt_reset(resets_at, now_ts)
            if t:
                reset_str = f" {C['dim']}({t}){C['reset']}"
        line2.append(f"{C['blue']}{label}{C['reset']} {bar}{reset_str}")

    # ── Line 3: 上轮 S×N Tok │ 本轮 S×N Tok │ Cached │ $cost │ dur ──
    line3 = []

    prev_tok_str = fmt_tokens(prev_round_tokens) if prev_round_tokens > 0 else C["dim"] + "--" + C["reset"]
    line3.append(
        f"{C['green']}上轮 S×{prev_stops}{C['reset']} "
        f"{C['peach']}{prev_tok_str}{C['reset']}"
    )

    curr_tok = fmt_tokens(curr_round_tokens) if curr_round_tokens > 0 else fmt_tokens(turn_in)
    line3.append(f"{C['green']}本轮 S×{curr_stops}{C['reset']} {C['peach']}{curr_tok}{C['reset']}")

    cache_read = curr.get("cache_read_input_tokens") or 0
    if cache_read > 0:
        line3.append(f"{C['green']}Cached{C['reset']} {C['cyan']}{fmt_tokens(cache_read)}{C['reset']}")

    usd = cost.get("total_cost_usd")
    if usd is not None:
        line3.append(f"{C['magenta']}${usd:.2f}{C['reset']}")

    duration_ms = cost.get("total_duration_ms")
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

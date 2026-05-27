#!/usr/bin/env bash
# 自动恢复 tt-statusline 的 statusLine 命令（防止 tt setup 覆盖）
# 注册为 Stop hook，每次 LLM 响应结束时运行

# 丢弃 Claude Code 传入的 stdin JSON（本脚本不需要）
cat > /dev/null

CONF="$HOME/.claude/tt-statusline-cmd.conf"
SETTINGS="$HOME/.claude/settings.json"

[[ -f "$CONF" ]] || exit 0

EXPECTED="$(cat "$CONF")"

CURRENT="$(python3 -c "
import json
try:
    cfg = json.load(open('$SETTINGS', encoding='utf-8'))
    sl = cfg.get('statusLine', {})
    print(sl.get('command', '') if isinstance(sl, dict) else '')
except:
    print('')
" 2>/dev/null)"

if [[ "$CURRENT" != "$EXPECTED" ]]; then
    python3 - "$CONF" "$SETTINGS" <<'PYEOF'
import json, sys
expected = open(sys.argv[1], encoding='utf-8').read().strip()
settings = sys.argv[2]
with open(settings, encoding='utf-8') as f:
    cfg = json.load(f)
cfg['statusLine'] = {'type': 'command', 'command': expected}
with open(settings, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PYEOF
fi

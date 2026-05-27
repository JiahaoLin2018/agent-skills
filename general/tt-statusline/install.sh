#!/usr/bin/env bash
# tt-statusline 安装脚本
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
HOOKS_DIR="${CLAUDE_DIR}/hooks"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"
HOOK_FILE="${HOOKS_DIR}/on-prompt-submit.sh"

# 1. 复制主脚本
cp "${SKILL_DIR}/scripts/tt-statusline.py" "${CLAUDE_DIR}/tt-statusline.py"
echo "[tt-statusline] 已安装 tt-statusline.py"

# 2. 更新 settings.json 中的 statusLine 配置
# 检测 python 路径（优先 anaconda3）
PYTHON_PATH="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")"
# Windows anaconda3 路径兼容
if [[ -f "/d/newSystemInstallDirection/anaconda3/python.exe" ]]; then
  PYTHON_PATH="D:/newSystemInstallDirection/anaconda3/python.exe"
fi

STATUS_CMD="bash -c '${PYTHON_PATH} ~/.claude/tt-statusline.py'"

# 使用 python3 更新 settings.json（避免 jq 依赖）
python3 - <<PYEOF
import json, os

settings_file = os.path.expanduser("~/.claude/settings.json")
with open(settings_file, encoding="utf-8") as f:
    cfg = json.load(f)

cfg["statusLine"] = {"type": "command", "command": "${STATUS_CMD}"}

with open(settings_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("[tt-statusline] 已更新 settings.json statusLine 配置")
PYEOF

# 3. 保存正确命令到配置文件（供 guard 脚本使用）
echo "${STATUS_CMD}" > "${CLAUDE_DIR}/tt-statusline-cmd.conf"
echo "[tt-statusline] 已保存 statusLine 命令到 tt-statusline-cmd.conf"

# 4. 安装 guard 脚本并注册为 Stop hook（防止 tt setup 覆盖 settings.json）
cp "${SKILL_DIR}/scripts/tt-statusline-guard.sh" "${HOOKS_DIR}/tt-statusline-guard.sh"
chmod +x "${HOOKS_DIR}/tt-statusline-guard.sh"
echo "[tt-statusline] 已安装 tt-statusline-guard.sh"

GUARD_CMD="bash ~/.claude/hooks/tt-statusline-guard.sh"
python3 - <<PYEOF
import json, os

settings_file = os.path.expanduser("~/.claude/settings.json")
with open(settings_file, encoding="utf-8") as f:
    cfg = json.load(f)

stop_hooks = cfg.setdefault("hooks", {}).setdefault("Stop", [])
guard_cmd = "${GUARD_CMD}"

already = any(
    h.get("command") == guard_cmd
    for entry in stop_hooks
    for h in entry.get("hooks", [])
)
if not already:
    stop_hooks.append({"matcher": "", "hooks": [{"type": "command", "command": guard_cmd}]})
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("[tt-statusline] 已注册 guard Stop hook")
else:
    print("[tt-statusline] guard Stop hook 已存在，跳过")
PYEOF

# 5. 在 on-prompt-submit.sh 末尾追加 flag 写入（如果尚未存在）
FLAG_LINE='echo "${SESSION_ID}" > "${HOME}/.claude/tt-new-round.flag" 2>/dev/null || true'

if [[ -f "${HOOK_FILE}" ]]; then
  if ! grep -qF "tt-new-round.flag" "${HOOK_FILE}"; then
    echo "" >> "${HOOK_FILE}"
    echo "# 通知 tt-statusline 新一轮开始" >> "${HOOK_FILE}"
    echo "${FLAG_LINE}" >> "${HOOK_FILE}"
    echo "[tt-statusline] 已追加 flag 写入到 ${HOOK_FILE}"
  else
    echo "[tt-statusline] on-prompt-submit.sh 已包含 flag 写入，跳过"
  fi
else
  echo "[tt-statusline] 警告：${HOOK_FILE} 不存在，请手动添加以下内容："
  echo "  ${FLAG_LINE}"
fi

echo "[tt-statusline] 安装完成，重启 Claude Code 生效"

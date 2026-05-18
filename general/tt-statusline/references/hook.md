# on-prompt-submit.sh Hook 说明

tt-statusline 依赖 `UserPromptSubmit` hook 在用户每次提问时写入一个 flag 文件，用于辅助检测新轮开始。

## 需要追加的代码

在 `~/.claude/hooks/on-prompt-submit.sh` 末尾追加以下内容：

```bash
# 通知 tt-statusline 新一轮开始，用于重置轮次计数
echo "${SESSION_ID}" > "${HOME}/.claude/tt-new-round.flag" 2>/dev/null || true
```

> `install.sh` 会自动完成此追加操作，无需手动添加。

## Hook 注册

`~/.claude/settings.json` 中需要有以下配置：

```json
"hooks": {
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "bash ~/.claude/hooks/on-prompt-submit.sh"
        }
      ]
    }
  ]
}
```

## 工作原理

1. 用户发送消息 → hook 触发，将当前 `session_id` 写入 `~/.claude/tt-new-round.flag`
2. Claude 响应结束（Stop 事件）→ `tt-statusline.py` 被调用
3. 脚本读取 flag 文件，检测到 session_id 匹配 → 判定为新轮开始，轮次计数归零
4. 删除 flag 文件，更新 `tt-round-state.json`

> **备注**：flag 文件方式是主检测手段之一。脚本同时还会读取 transcript JSONL 中的 `last-prompt` 条目数作为双保险，两种方式都会同步更新 `last_prompt_count`，避免同一轮内重复触发。

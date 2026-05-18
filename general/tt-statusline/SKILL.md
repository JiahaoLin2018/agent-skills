---
name: tt-statusline
description: Claude Code 状态栏 token 追踪器。包含安装脚本和主脚本，不通过 slash command 调用，仅作为配置打包使用。
disable-model-invocation: true
---

# tt-statusline — Claude Code 状态栏 token 追踪器

状态栏实时显示 token 用量、LLM 交互次数、速率限制、费用等信息。

## 文件结构

```
skills/tt-statusline/
├── SKILL.md
├── install.sh            # 一键安装脚本
├── scripts/
│   └── tt-statusline.py  # 状态栏主脚本
└── references/
    └── config.md         # 字段说明与实现要点
```

## 安装

```bash
bash ~/.claude/skills/tt-statusline/install.sh
```

安装脚本会：
1. 将 `tt-statusline.py` 复制到 `~/.claude/`
2. 更新 `~/.claude/settings.json` 中的 `statusLine` 配置
3. 在 `~/.claude/hooks/on-prompt-submit.sh` 末尾追加 flag 写入代码

## 效果预览

```
[Sonnet 4.6 | Max] │ ◑ 27% │ S×3 54k │ [jiahao]
5h ██░░░░░░ 28% (2h0m · 12:00) │ 7d ░░░░░░░░ 2% (4d22h · 05/23 08:00)
上轮 S×2 102 │ 本轮 S×1 105 │ Cached 53k │ $6.59 │ 2d16h
```

详细字段说明见 `references/config.md`。

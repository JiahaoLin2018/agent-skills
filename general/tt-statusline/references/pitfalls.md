# tt-statusline 踩坑记录

## `tt setup` 会覆盖 settings.json 中的 statusLine 命令

**现象**：运行 `tt setup`（token-tracker 的配置命令）后状态栏消失。

**原因**：`tt setup` 同时做两件事：
1. 覆盖 `~/.claude/tt-statusline.py`（已通过 `__version__ = "1.5"` 规避，见 config.md 实现要点 8）
2. **覆盖 `settings.json` 的 `statusLine` 命令**——改成直接调用 Windows python.exe：

```json
"statusLine": {
  "type": "command",
  "command": "D:\\...\\python.exe C:\\Users\\jh/.claude/tt-statusline.py"
}
```

在 Windows 下，Claude Code 用这种方式调用时 stdin 管道无法正常传入 JSON，脚本收到空数据静默退出，状态栏消失。

**修复**：把 `settings.json` 的 `statusLine` 命令改回 `bash -c` 包装格式：

```json
"statusLine": {
  "type": "command",
  "command": "bash -c 'D:/newSystemInstallDirection/anaconda3/python.exe ~/.claude/tt-statusline.py'"
}
```

**结论**：`tt setup` 运行后必须手动修复 `settings.json`，或重新执行 `install.sh`。

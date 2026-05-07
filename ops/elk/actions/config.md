# Action: config

原文输出当前配置文件供用户核查。

## 命令格式

```
/elk config
```

## 步骤

1. **加载配置（含自动检测）**：

   按 SKILL.md"配置加载流程"执行：检查配置文件是否存在，不存在则从模板自动创建。

   ```bash
   test -f ~/.claude/skill_config_elk.yml || cp <skill_dir>/templates/skill_config_elk-template.yml ~/.claude/skill_config_elk.yml
   ```

2. **读取并展示配置文件（密码脱敏）**：

   使用 `elk_api.py config` 子命令读取配置并自动将 `password` 字段脱敏为 `***`，避免在终端 / 截屏 / 日志中泄漏密码：

   ```bash
   python <skill_dir>/scripts/elk_api.py config
   ```

   若用户明确需要查看原文（如核对密码），引导用户自己执行：
   ```bash
   cat ~/.claude/skill_config_elk.yml
   ```
   并提醒注意终端历史与屏幕共享。

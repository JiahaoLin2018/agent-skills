# Action: indices

列出 Elasticsearch 中所有可用索引。

## 命令格式

```
/elk indices
/elk indices uat
```

## 步骤

1. **加载配置（含自动检测）**：

   按 SKILL.md"配置加载流程"执行：检查配置文件是否存在，不存在则从模板自动创建。

   ```bash
   test -f ~/.claude/skill_config_elk.yml || cp <skill_dir>/templates/skill_config_elk-template.yml ~/.claude/skill_config_elk.yml
   ```

2. **确定环境**：默认列出生产环境索引；用户输入含 `uat`/`测试` 关键词则列测试环境。

3. **执行查询**：
   ```bash
   # 生产环境（默认）
   python <skill_dir>/scripts/elk_api.py --connection prod indices

   # 测试环境
   python <skill_dir>/scripts/elk_api.py --connection uat indices
   ```

4. **格式化输出**：按名称排序展示索引列表。

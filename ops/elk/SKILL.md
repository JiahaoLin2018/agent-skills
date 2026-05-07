---
name: elk
description: ELK 日志分析助手 — 查日志、查报错、查异常、ES 查询、Elasticsearch 日志分析。通过自然语言查询 Elasticsearch 日志，支持中文项目名模糊匹配、生产/测试环境切换、traceId 关联追踪和 AI 根因诊断。当用户提到"查日志"、"看报错"、"错误日志"、"异常日志"、"ES"、"ELK"、"traceId"、"链路追踪"时触发。
argument-hint: "[项目名] [环境] <自然语言描述> | help | indices | config | ping"
disable-model-invocation: true
---

# ELK 日志分析助手

> **路径约定**：`<skill_dir>` 指本 SKILL.md 所在目录。

你是 ELK 日志分析助手。帮助用户通过自然语言查询 Elasticsearch 日志，支持中文项目名模糊匹配、生产/测试环境切换、traceId 关联追踪和 AI 根因诊断。

## 文档职责说明

每个 skill 包含两份核心文档，面向不同读者：

| 文档 | 读者 | 职责 |
|------|------|------|
| **SKILL.md** | Claude Code（AI） | 技能执行指令 — 定义 frontmatter、action 路由、执行流程，Claude 据此响应 `/elk` 命令 |
| **README.md** | 人（开发者/用户） | 入门指引文档 — 按"安装教程 → 配置说明 → 功能介绍 → 使用示例"组织，是用户了解和上手该 skill 的唯一入口 |

> **原则**：安装步骤、配置教程、使用说明等面向人的内容写在 `README.md`；Claude 执行所需的指令逻辑写在 `SKILL.md`。两者不重复。

## 配置

脚本和模板位于本 Skill 目录下：
- `scripts/elk_api.py` — ES API 调用脚本
- `templates/` — 配置文件模板

用户配置文件：`~/.claude/skill_config_elk.yml`（含 ES 连接信息与项目配置）

> **配置文件命名规范**：所有 skill 的配置文件统一放在 `~/.claude/` 根目录下，命名为 `skill_config_<skill_name>.<ext>`（ext 按需选择，如 `.sh`、`.yml`）。配置文件不在 skill 安装目录内，因此不受 install/sync 影响。

## 配置加载流程

所有 action 在执行前统一按以下流程加载配置（具体命令见各 action 文件）：

1. **确保配置文件存在**：检查 `~/.claude/skill_config_elk.yml`，不存在则从 `<skill_dir>/templates/skill_config_elk-template.yml` 自动复制并告知用户修改连接信息
2. **检查 projects 配置**：无已启用项目时提示使用 defaults 配置，建议用 `/elk indices` 发现可用索引
3. **继续执行 action**：使用已有配置（含默认值）

## 用法

```
/elk <自然语言描述>
/elk <项目名/中文名> <自然语言描述>
/elk <项目名> <环境> <自然语言描述>
/elk help | indices | config | ping
```

## Actions

| 参数 | Action | 说明 |
|------|--------|------|
| `help` | actions/help.md | 展示所有已配置项目概览 |
| `indices` | actions/indices.md | 列出可用索引 |
| `ping` | actions/ping.md | 检查集群连通性 |
| `config` | actions/config.md | 查看当前配置文件 |
| 其他 | actions/query.md | 自然语言查询并分析日志 |

## 执行流程

收到 `/elk <action>` 命令后：
1. 根据上方 Actions 表确定目标 action
2. **读取** `<skill_dir>/actions/<action>.md` 获取该 action 的详细执行步骤
3. 按步骤执行

## 重要说明

- **默认环境是 prod**，明确说测试/uat 才切换
- **默认返回全部字段**，确保分析完整
- 项目模糊匹配命中多个时，**必须询问用户**再执行查询，不要自行猜测
- 密码等敏感信息不在回复中重复显示
- 依赖 **Python 3.6+**，脚本通过 `python` 或 `python3` 调用

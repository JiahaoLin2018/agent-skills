# ELK Analyzer — 入门指引

通过自然语言查询 Elasticsearch 日志，支持时间范围筛选、字段选择、traceId 关联分析和 AI 诊断。

## 安装教程

在 claudework 仓库根目录下运行：

```bash
bash elk/install.sh
```

脚本会将 `elk/` 全部内容复制到 `~/.claude/skills/elk/`。

### 安装后配置

**1. 创建配置文件**（首次安装时）：
```bash
cp ~/.claude/skills/elk/templates/skill_config_elk-template.yml ~/.claude/skill_config_elk.yml
chmod 600 ~/.claude/skill_config_elk.yml   # 保护密码，仅本人可读
```

> 若 `~/.claude/skill_config_elk.yml` 已存在则跳过，避免覆盖已有配置。

**2. 编辑配置**：填写 ES 连接信息和项目索引模式：
```bash
$EDITOR ~/.claude/skill_config_elk.yml
```

**3. 检查 Python3 环境**：
```bash
python3 --version   # 需要 Python 3.6+
```

**4. 验证连接**：
```bash
python3 ~/.claude/skills/elk/scripts/elk_api.py --connection prod ping
```

## 配置说明

配置文件：`~/.claude/skill_config_elk.yml`（安装时从模板复制，建议 `chmod 600` 保护密码）

> **注意**：本工具连接的是 **ELK 日志库**（Elasticsearch），用于查询应用运行日志，**不是业务数据库**。日志由 Logstash/Filebeat 从应用服务器采集后写入 ES。

### 如何获取 ES 连接地址

| 方式 | 说明 |
|------|------|
| 找运维/DevOps 同事 | 最直接的方式，获取 ES 地址、端口和只读账号 |
| Kibana 界面 | Management → Stack Monitoring 可查看集群地址 |
| 内部文档/Wiki | 搜索"Elasticsearch"或"ELK"相关的部署文档 |

地址格式为 `http://<host>:<port>`，默认端口 `9200`。

### 参数详解

**connections** — ES 集群连接信息：

| 参数 | 说明 |
|------|------|
| `uri` | Elasticsearch 访问地址，含协议和端口（如 `http://es-host:9200`） |
| `username` | ES 登录用户名（通常为 `elastic` 或运维分配的只读账号） |
| `password` | ES 登录密码（文件建议 `chmod 600` 仅本人可读） |

**defaults** — 默认查询参数（未在查询中指定时使用）：

| 参数 | 说明 |
|------|------|
| `prod_connection` | 生产环境使用的连接名（对应 connections 中的 key） |
| `prod_index` | 生产环境默认索引模式（支持通配符 `*`） |
| `uat_connection` | 测试环境使用的连接名 |
| `uat_index` | 测试环境默认索引模式 |
| `default_env` | 未指定环境时的默认值（`prod` 或 `uat`） |

**projects** — 项目配置（每个项目可指定独立的连接和索引）：

| 参数 | 说明 |
|------|------|
| `name_zh` | 项目中文名（用于显示） |
| `aliases` | 别名列表，逗号分隔（支持中文/缩写，用于模糊匹配） |
| `description` | 项目简要描述 |
| `prod_connection` | 该项目生产环境的连接名 |
| `prod_index` | 该项目生产环境的日志索引模式（用 `/elk indices` 查看可用索引） |
| `uat_connection` | 该项目测试环境的连接名 |
| `uat_index` | 该项目测试环境的日志索引模式 |

### 配置示例

```yaml
connections:
  prod:
    uri: http://YOUR_PROD_ES_HOST:9200
    username: elastic
    password: <your-password>
  uat:
    uri: http://YOUR_UAT_ES_HOST:9200
    username: elastic
    password: <your-password>

defaults:
  prod_connection: prod
  prod_index: app-prod-*
  uat_connection: uat
  uat_index: app-uat-*
  default_env: prod

projects:
  my-service:
    name_zh: "我的服务"
    aliases: "myservice,我的服务,my"
    description: "服务描述"
    prod_connection: prod
    prod_index: app-prod-*
    uat_connection: uat
    uat_index: app-uat-*
```

### 项目模糊匹配规则

用户说"我的服务项目"时，匹配优先级：
1. 精确匹配 key（`my-service`）
2. 精确匹配 name_zh（`我的服务`）
3. 匹配任意 alias（在 `aliases` 字段中定义的别名）
4. 前缀匹配 key（`my-` 可匹配多个项目）
5. 多个匹配 → 列出候选项，询问用户

### 索引发现

不需要预先填好所有索引名 —— 配好 ES 连接后用 `/elk indices` 自动发现现有索引，再按需配置到 `projects.<project>.prod_index` 中。

### 目录结构

```
elk/
├── SKILL.md              # Skill 主文件 — Claude 读取此文件执行指令
├── README.md             # 入门指引文档 — 安装、配置、功能、示例
├── install.sh            # 通用安装脚本
├── CHANGELOG.md          # 变更日志
├── actions/              # 各 action 详细步骤
├── evals/                # 触发测试用例（Description 优化时复用）
├── references/           # 参考文档（查询报告格式规范等）
├── scripts/              # 辅助脚本（elk_api.py）
└── templates/            # 配置文件模板
```

## 功能介绍

| Action | 命令 | 说明 |
|--------|------|------|
| query | `/elk <自然语言描述>` | 自然语言查询并分析日志 |
| help | `/elk help` | 展示所有已配置项目概览 |
| indices | `/elk indices` | 列出可用索引 |
| ping | `/elk ping [env]` | 检查集群连通性 |
| config | `/elk config` | 查看当前配置文件 |

### 自然语言查询
用中文描述你的需求，Claude 自动转换为 ES DSL：
- "查一下昨天下午3点到5点的错误日志"
- "最近1小时有哪些 NullPointerException"
- "今天上午用户登录接口超时的日志"

### 时间范围筛选
支持相对时间和绝对时间，自动处理时区（UTC+8）：
- 相对：`最近1小时`、`今天`、`昨天`、`最近30分钟`
- 绝对：`2024-01-15 15:00 到 17:00`

### 字段选择
按需返回日志字段，减少噪音：
- 快速排查：`@timestamp, logger, traceId, message`
- 多机排查：追加 `ip, host.name`
- 完整日志：不限制字段

### traceId 关联分析
发现 traceId 后自动提示，一键获取完整请求调用链：
- 查询同一 traceId 的所有日志
- 按时间排序还原请求链路
- 支持最多 2000 条关联日志

### 聚合统计
按字段分组统计数量，适用于统计各类错误分布：
- 按日志级别统计：`/elk 统计今天各级别日志数量`
- 按 Logger 统计：`/elk 统计最近1小时各类异常来源`
- 按主机统计：`/elk 今天各实例的错误数量`

### 连接健康检查
验证 Elasticsearch 连接是否正常：
- `/elk ping` — 检查生产环境连通性及集群状态
- `/elk ping uat` — 检查测试环境

### AI 诊断分析
获取日志后自动分析：
- 问题摘要：错误类型、影响范围
- 根因推断：从日志内容推断可能原因
- 建议处理：具体的排查步骤和修复建议

### 配置型多项目
在配置文件中定义多个服务的索引模式，查询时按项目名自动切换：
```
/elk my-service 查最近1小时的超时日志
/elk order-service 查昨天的错误日志
```

### 可用字段

| 字段 | 说明 |
|------|------|
| `@timestamp` | 日志时间戳（UTC） |
| `logger` | Java Logger 类名 |
| `traceId` | 链路追踪 ID |
| `thread` | 线程名 |
| `message` | 日志内容 |
| `codeline` | 产生日志的代码行 |
| `ip` | 服务器 IP |
| `host.name` | 主机名 |
| `fields.logtype` | 日志类型标签 |
| `log.file.path` | 日志文件路径 |

## 使用示例

### 基础查询
```
/elk 查一下最近1小时的错误日志
```

### 指定项目
```
/elk my-service 今天上午通知失败的日志
/elk 我的服务 最近1小时登录超时的日志
/elk my-service uat 最近1小时的 NullPointerException
```

### traceId 追踪
```
/elk 查找 traceId=abc123 的完整调用链
```

### 异常排查
```
/elk 最近30分钟有哪些 NullPointerException，是哪个类抛出的
```

### 聚合统计
```
/elk 统计今天各类错误的数量
/elk 统计最近1小时各 Logger 的错误数量
```

### 连接健康检查
```
/elk ping
/elk ping uat
```

### 索引发现
```
/elk indices
```

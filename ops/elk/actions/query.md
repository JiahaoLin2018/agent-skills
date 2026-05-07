# Action: query

自然语言查询 Elasticsearch 日志，输出结构化分析报告。

## 命令格式

```
/elk <自然语言描述>
/elk <项目名/中文名> <自然语言描述>
/elk <项目名> <环境> <自然语言描述>
```

## 步骤

### 阶段一：项目识别与环境确定

### 1.1 加载配置，提取所有项目

按 SKILL.md"配置加载流程"执行：确保配置文件存在，不存在则从模板自动创建并提示用户修改连接信息。

```bash
test -f ~/.claude/skill_config_elk.yml || cp <skill_dir>/templates/skill_config_elk-template.yml ~/.claude/skill_config_elk.yml
cat ~/.claude/skill_config_elk.yml
```

读取配置后，构建如下项目检索表（供匹配使用）：

| key | name_zh | aliases（逗号分隔） | description |
|-----|---------|-------------------|-------------|
| my-service | 我的服务 | myservice,我的服务,my | ... |
| ... | ... | ... | ... |

### 1.2 项目模糊匹配

用户输入的项目词（中文/英文/缩写）按以下优先级依次匹配：

1. **精确匹配 key** — 用户输入 = 项目 key（如 `my-service`）
2. **精确匹配 name_zh** — 用户输入 = name_zh（如 `我的服务`）
3. **匹配任意 alias** — 用户输入包含或等于某个 alias 词（如 `myservice` → alias 包含 `myservice`）
4. **前缀匹配 key** — 用户输入是某个 key 的前缀（如 `my-` 可匹配 `my-service` 和 `my-admin`）

#### 匹配结果处理

**唯一匹配** → 直接使用该项目，继续执行。

**多个匹配** → 列出候选项，让用户确认：

```
找到以下与「my」相关的项目，请确认：

  1. my-service — 我的服务（前端/API 入口服务）
  2. my-admin   — 我的后台管理系统

请问是哪个项目的日志？
```

**未匹配** → 提示用户：

```
未找到与「xxx」匹配的项目配置。

当前已配置的项目：
  - my-service（我的服务）
  - ...

请确认项目名，或使用 /elk indices 查看当前可用索引。
```

**未指定项目** → 使用 `defaults` 配置中对应环境的连接和索引。

### 1.3 环境识别

| 用户描述 | 环境 |
|---------|------|
| `uat`、`测试`、`测试环境`、`dev`、`fat`、`开发环境` | uat |
| `prod`、`生产`、`线上`、`生产环境` | prod |
| **未提及** | **默认 prod** |

### 1.4 确定连接和索引

```
env = prod → connection = projects.<key>.prod_connection
             index     = projects.<key>.prod_index
env = uat  → connection = projects.<key>.uat_connection
             index     = projects.<key>.uat_index
```

---

## 阶段二：查询构造与执行

> **注意**：`--connection` 是全局参数，必须放在子命令之前。

> **并行调用指导**：以下查询之间的依赖关系决定了哪些可以并行：
>
> | 可并行的组合 | 说明 |
> |------------|------|
> | 2.0 字段探测 | 独立执行，无依赖 |
> | count + search(最早) + search(最新) | 三者互不依赖，可同时发起 |
> | 多个 aggs（projectname / loglevel / ip） | 互不依赖，可同时发起 |
>
> | 必须串行的步骤 | 原因 |
> |--------------|------|
> | 2.0 → 2.0.1 及后续 | 需要先确认字段名才能构造 DSL |
> | 2.0.1 时间边界 → 2.4.1 随机抽样 | 抽样必须使用探测到的实际时间窗口 |

### 2.0 字段探测（首次查询该项目时必须执行）

**在构造任何 DSL 之前**，先取 1 条样本确认实际字段名，避免后续查询字段名写错：

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" search \
  --index "<index_pattern>" \
  --query '{"match_all":{}}' \
  --from "now-1h" \
  --to "now" \
  --size 1
```

从返回结果中确认以下字段的**实际名称**，并在后续查询中使用实际值：

| 用途 | 可能的字段名 | 确认后使用 |
|------|------------|----------|
| 消息内容 | `msg` / `message` / `rest` | 第一个非空的 |
| 日志级别 | `loglevel` / `severity` / `level` | 实际存在的 |
| traceId  | `traceId` / `trace` / `trace_id` | 实际存在的 |
| Logger   | `logger` / `class` / `classname` | 实际存在的 |

> 若 `now-1h` 无数据，改为 `now-24h`。若仍无数据，跳过此步骤。

### 2.0.1 时间边界探测（宽时间范围时必须执行）

当查询时间范围 ≥ 4 小时（如「今天」「最近24小时」「昨天」）时，在构造业务查询之前，**并行**取最早和最新记录以确定数据的实际时间窗口：

```bash
# 以下两条命令并行执行
python <skill_dir>/scripts/elk_api.py --connection "<connection>" search \
  --index "<index_pattern>" \
  --query '<用户业务DSL>' \
  --from "<time_from>" \
  --to "<time_to>" \
  --size 1 --sort asc

python <skill_dir>/scripts/elk_api.py --connection "<connection>" search \
  --query '<用户业务DSL>' \
  --index "<index_pattern>" \
  --from "<time_from>" \
  --to "<time_to>" \
  --size 1 --sort desc
```

从结果中提取：
- **数据起始时间** = 升序第 1 条的 `@timestamp`（转 CST）
- **数据结束时间** = 降序第 1 条的 `@timestamp`（转 CST）
- **实际时间窗口** = 起始 — 结束

> 此步骤可与 `count` 命令并行执行（count 不依赖时间边界结果）。
>
> 若总量为 0，直接报告「该时间范围内无匹配数据」，跳过后续所有阶段。
>
> 后续所有需要指定时间段的操作（抽样、分时段统计等），**必须在此实际窗口内操作**，不得盲目猜测时间段。

### 2.1 关键词搜索

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" search \
  --index "<index_pattern>" \
  --query '<ES_DSL_JSON>' \
  --from "<time_from>" \
  --to "<time_to>" \
  --size <num>
```

### 2.2 traceId 关联查询

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" trace \
  --index "<index_pattern>" \
  --traceid "<traceId_value>" \
  --from "<time_from>" \
  --to "<time_to>"
```

### 2.3 统计数量

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" count \
  --index "<index_pattern>" \
  --query '<ES_DSL_JSON>' \
  --from "<time_from>" \
  --to "<time_to>"
```

### 2.4 聚合统计（按字段分组计数）

适用于"统计各类错误数量"、"各实例错误分布"等需求，优先于 `count` 命令。

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" aggs \
  --index "<index_pattern>" \
  --field "<field_name>" \
  --query '<ES_DSL_JSON>' \
  --from "<time_from>" \
  --to "<time_to>" \
  --top <num>
```

**常用聚合字段**：

| 用户需求 | `--field` 值 |
|---------|-------------|
| 各级别（ERROR/WARN/INFO）数量 | `loglevel.keyword` 或 `severity.keyword`（以 2.0 探测结果为准） |
| 各 Logger/类 的错误数量 | `logger.keyword` 或 `class.keyword` |
| 各实例/主机 的错误数量 | `ip` 或 `host.name` |
| 各异常类型 | `exception.keyword` |

> 聚合字段必须用 `.keyword` 后缀（对 text 类型字段），否则 ES 会报错。若字段本身是 keyword 类型则无需加。实际字段名以 2.0 探测结果为准。

**输出格式**：
```json
{
  "total": 1234,
  "field": "loglevel.keyword",
  "buckets": [
    {"key": "ERROR", "count": 89},
    {"key": "WARN",  "count": 312}
  ]
}
```

### 2.4.1 随机抽样

当用户要求「随机抽一个」「看个例子」「抽样看看」时，使用 ES `function_score` + `random_score` 实现真随机，**不要通过猜测时间段来抽样**：

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" search \
  --index "<index_pattern>" \
  --query '{"function_score":{"query":<用户业务DSL>,"random_score":{}}}' \
  --from "<actual_start>" \
  --to "<actual_end>" \
  --size 1
```

**关键规则**：
- `<actual_start>` 和 `<actual_end>` 必须使用 2.0.1 步骤探测到的**实际时间窗口**，不得使用「今天」等宽泛范围外的时间
- `random_score` 无需参数，ES 会自动生成随机分数
- 若 `function_score` 查询报错（部分旧版 ES 不支持），**降级方案**：在实际时间窗口的中间时间点附近取 1 条
  ```
  中间时间 = actual_start + (actual_end - actual_start) / 2
  --from "<中间时间 - 5min>" --to "<中间时间 + 5min>" --size 1
  ```

### 2.5 列出索引

```bash
python <skill_dir>/scripts/elk_api.py --connection "<connection>" indices --pattern "<pattern>"
```

### 2.6 ES DSL 构造

**时间格式**（用户时间为 CST = UTC+8，加 `+08:00`）：

| 用户描述 | ES 表达式 |
|---------|---------|
| 最近1小时 | `now-1h` / `now` |
| 今天 | `now/d` / `now` |
| 昨天 | `now-1d/d` / `now/d` |
| 今天下午3-5点 | `今日T15:00:00+08:00` / `今日T17:00:00+08:00` |
| 2024-01-15 15:00 | `2024-01-15T15:00:00+08:00` |

**查询命令选择规则（重要）**：

| 用户输入特征 | 使用命令 | 说明 |
|------------|---------|------|
| 明确说 `traceId=xxx`、`追踪链路`、`完整调用链` | `trace` | 按 traceId 追踪链路 |
| 其他一切情况（ID、编号、关键词、异常信息等） | `search` | **默认搜消息字段** |

> **关键原则**：用户给出任何搜索值（无论是 ID、业务编号、错误信息还是看起来像 traceId 的字符串），**一律默认用 `search` 命令在消息字段中搜索**，不要自行判断为 traceId。只有用户明确说"追踪 traceId"时才用 `trace` 命令。

**消息字段搜索 DSL**（`msg`/`message`/`rest` 以 2.0 探测结果为准）：

```json
// 在消息字段中搜索关键词（默认方式）
{"bool": {"must": [{"match_phrase": {"msg": "<用户给的值>"}}]}}

// 若 msg 无结果，依次尝试 message、rest
{"bool": {"must": [{"match_phrase": {"message": "<用户给的值>"}}]}}
```

**其他常用 DSL 模板**：

```json
// 错误日志（按级别筛选）
{"bool": {"must": [{"term": {"loglevel.keyword": "ERROR"}}]}}

// 异常类型（精确短语）
{"bool": {"must": [{"match_phrase": {"msg": "NullPointerException"}}]}}

// 特定 Logger
{"bool": {"must": [{"match_phrase": {"logger": "UserService"}}]}}

// 多条件
{"bool": {"must": [{"match_phrase": {"msg": "timeout"}}, {"match_phrase": {"logger": "feign"}}]}}

// 全部（无关键词）
{"match_all": {}}
```

时间范围通过 `--from`/`--to` 传入，不放入 DSL。

**默认返回所有字段**（不加 `--fields`），以获取完整信息用于分析。用户明确指定字段时才使用 `--fields`。

**排序方向**：根据用户意图选择，不固定升序：

| 用户描述含以下词 | 排序 | 说明 |
|--------------|------|------|
| 最近、刚刚、最新、now | `desc`（降序） | 最新的在前，适合「看最近有没有报错」 |
| 追踪、从头、时间线、调用链、完整链路 | `asc`（升序） | 时间正序，适合还原请求过程 |
| 未明确 | `desc`（降序） | 默认展示最新，符合排障直觉 |

`search` 命令通过 `--sort` 参数传入（elk_api.py 内置支持），或直接在 DSL 外由调用参数控制：
```bash
# 降序（最新在前，默认推荐）
python ... search ... --sort desc

# 升序（时间线还原）
python ... search ... --sort asc
```

---

## 阶段三/四/五：报告输出

查询完成后，按 `<skill_dir>/references/report-format.md` 中定义的格式依次输出：
1. **标准汇报头**（查询信息 + 统计概览）
2. **日志明细**（逐条展示，超 50 条截断）
3. **分析报告**（问题摘要 → 根因分析 → 影响范围 → 关键时间线 → 建议处理）

执行前读取该文件获取完整格式规范。

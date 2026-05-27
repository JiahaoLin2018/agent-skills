---
name: synthesize-prd
description: Synthesize a structured Product Requirements Document (PRD) from established conversation consensus, without re-interviewing the user. Use this skill IMMEDIATELY after /brainstorming and /grill-me have converged and the user wants the requirements documented. Triggers on phrases like "write the PRD", "合成 PRD", "落规格", "生成需求文档", "把需求写下来", "出 PRD", "OK 这样定了写文档", or any signal that the discovery/discussion phase is complete and a formal document is needed. Outputs to a local markdown file with two parts (Requirements + System Design), embeds Deep Module identification, and produces extensive User Stories + Acceptance Criteria. Does NOT publish to any issue tracker — purely local-file workflow. Make sure to use this skill whenever the user wants to lock in requirements after brainstorming, even if they don't explicitly say "PRD" — phrases like "we're done discussing, document this", "已达成共识，请落规格", or "把刚才聊的写成文档" should also trigger.
---

# Synthesize PRD

把 brainstorming + grill-me 在对话中收敛的全部决策，合成一份结构化的 PRD。**不再向用户提问任何问题** —— 完全基于已有对话上下文 + 代码库探索。

本 skill 是 **mattpocock/to-prd 的本地化替代** —— 同样的「合成不采访」哲学 + Deep Module 思维 + 详尽 User Stories，但**不绑定任何 issue tracker**，产物只落本地 markdown 文件。

> 本文件是 single-file skill —— 规则 / 示例 / 模板 / CHANGELOG 全在这里。AI 触发后只读这一个文件，不需要额外 Read。

---

## 1. 何时调用

**前置条件**（全部满足才调用）：

- `/brainstorming` 已完成，业务/技术方案在对话中达成共识
- `/grill-me` 已追问完所有决策树分支，无未决点
- 用户明确表达「写 PRD」「合成需求文档」「落规格」「把需求写下来」等同义意图

**禁止调用**：

- ❌ 对话尚未充分发散收敛（需求模糊）→ 回 `/brainstorming`
- ❌ 仍有未决决策点 → 回 `/grill-me`
- ❌ 已存在 prd.md 仅小修小补 → 直接 Edit，不调本 skill

---

## 2. 硬约束（Hard Rules）

每条约束都附原因，目的是让你理解为什么这么做，而不是机械执行。

### 2.1 不再向用户提问

- **原因**：这叫「合成 skill」是因为 brainstorming + grill-me 已经把信息挖透了。如果再问问题，本质上是让用户重复输入，违反「合成模式」的精髓。
- **怎么做**：信息只从三个来源取 ——（a）当前对话上下文（brainstorming + grill-me 沉淀的决策）；（b）代码库探索（架构约束 / 现有命名 / 术语词汇）；（c）项目文档（Glob 扫项目文档目录，不依赖硬编码文件名）。

### 2.2 不推送任何 issue tracker

- **原因**：本地化产物方便 git 管理 + 跨阶段引用 + 离线编辑。mattpocock/to-prd 默认推 GitHub Issue 的行为对很多场景不适用（原型期、内部项目、不用 issue tracker 的团队）。
- **怎么做**：不调 GitHub/GitLab/Linear API，不创建 issue，不打 label，不需要任何外部 tracker 配置。

### 2.3 不写代码（有两类例外）

- **原因**：PRD 终态是评审用的需求文档，整段业务逻辑代码会让业务方评审跑偏，且代码很快过时。
- **主规则**：不在 prd.md 内嵌**完整可执行的业务逻辑代码**（如完整的 service / controller / handler 实现）。

**反例（禁止写这种）**：
```typescript
// ❌ 完整可执行业务逻辑(PRD 不是开发文档)
export class QuotaApplyService {
  async submit(application: QuotaApply): Promise<Result> {
    const validated = await this.validator.validate(application);
    const saved = await this.db.insert(validated);
    await this.eventBus.publish(new QuotaSubmitted(saved));
    return Result.ok(saved);
  }
}
// → 完整 service 代码归 plan/execute 阶段,不写进 PRD
```

#### 例外 1：结构性精确表达（来自 mattpocock/to-prd）

- **适用**：类型定义 / 枚举 / schema / 状态机转换字典 / reducer 结构
- **要求**：trimmed 到只剩**决策关键部分**，不是可运行的 demo
- **目的**：锁定决策精确性（这个状态机就这么转，不可商量）

**示例**：
```typescript
// ✅ 类型定义(锁状态空间)
type QuotaStatus = 'draft' | 'submitted' | 'approved' | 'rejected';

// ✅ 状态机转换字典(锁迁移路径)
const STATE_TRANSITIONS = {
  draft: ['submitted', 'cancelled'],
  submitted: ['approved', 'rejected'],
  approved: [],  // 终态
  rejected: [],  // 终态
};
```

#### 例外 2：伪代码 / 算法草图

- **适用**：关键算法、复杂业务规则的实现流程、外部 API 集成步骤
- **要求**：**伪代码或精简版**，让开发知道"大概这么实现"，不限定具体写法
- **目的**：指实现方向（开发可优化具体写法，但业务逻辑得对）

**示例**：
```
// ✅ 关键算法伪代码(指实现方向)
calculateApprovalAmount(application):
  if creditScore > 700:
    return requestedAmount        # 信用好,全额批
  else:
    return requestedAmount * 0.8  # 信用差,8 折批
```

### 2.4 不画流程图

- **原因**：流程图归独立的图表生成 skill（如 `/baoyu-diagram`）。PRD 评审通过后才画图，这样图与 PRD 内容保持同步，避免「PRD 改了图没改」。
- **怎么做**：本 skill 只在 PRD 的「业务流程」section 留图占位（相对路径引用如 `diagrams/state-machine.svg`），不生成 SVG。

---

## 3. 流程

### Step 1: 探索项目上下文（尊重既有命名）

**用 Glob 扫描，不硬编码具体文件**：

- `Glob docs/*.md` —— 拿到所有顶层项目文档（产品定位 / 工程约束 / 业务参考等），逐一读完建立完整理解
- `Glob docs/business-design/*.md` 等业务子目录 —— 业务设计沉淀（如存在）
- 历史需求目录 `docs/stories/` —— 读**最近 1-2 个**已完成的 PRD，了解上一阶段做了什么可能与本次相关
- 业务相关的源码目录（如 `src/features/**`, `src/modules/**`）—— 复用既有命名

**特别注意以下两类文档**（来自 mattpocock/to-prd 的最佳实践）：

#### 1. 术语词汇表（domain glossary）

在项目文档中找到 glossary（常见位置 `docs/product.md §术语`、`docs/glossary.md`、`README.md` 等）；**贯穿整个 PRD 使用项目原生术语**，不另造词。

**正反对照示例**：
```
✅ 用项目原生术语:
   「客户企业管理员审批授信申请」
   (项目 glossary 定义:客户企业 / 授信申请)

❌ 临时造词:
   「合作企业管理者批准额度需求」
   (项目无"合作企业"概念,"额度需求"不是项目术语)
```

#### 2. 架构决策记录（ADR）

如项目有 ADR 目录（`docs/adr/`、`docs/decisions/`、`docs/architecture/`），**所有 ADR 必须 respect**；与 ADR 冲突的需求设计是大错，应该回 brainstorming 重谈而不是写进 PRD。

**ADR 冲突示例**：
```
PRD §9 数据模型想写「新增 events 表存储用户操作日志」
但 ADR-007 规定「不再新增表,事件统一走 event_log.payload JSON 字段」
→ ❌ 冲突! 不能写进 PRD
→ ✅ 应回 brainstorming 重谈,要么改方案符合 ADR,要么提议修订 ADR
```

**为什么不硬编码具体文件名**：项目持续演进会新增文档，扫描机制让新文档自动纳入，避免本 skill 滞后于项目文档结构。

**禁止动作**：不修改任何文件，只读。

### Step 2: 识别 Deep Module

按 John Ousterhout 的「Deep Module」原则识别本次需求的核心模块：

> Deep Module = 封装大量功能 + 暴露简单接口 + 接口很少变更

对每个候选模块在 PRD 中体现：

- 模块名 + 一句话职责
- 暴露给上游的接口签名（用 API 列表 + 表结构表达）
- 不与用户确认，直接写进 PRD「数据模型」+「API 设计」section

### Step 3: 推断需求编号与目录名

PRD 输出到 `docs/stories/<NN>-<name>/prd.md`，约定：

- `<NN>` 两位数字（01, 02, ..., 99）—— 看现有 `docs/stories/` 子目录中最大的 NN，新需求用 NN+1
- `<name>` 英文 kebab-case（如 `user-login`, `payment-flow`, `quota-apply`）
- 同阶段不同子需求用**字母后缀**（如 `03b`, `03c`, `07b`）
- 若用户在对话中明确指定了编号，按用户的来

> `docs/stories/` 是 Agile 通用工程约定（"User Story" 概念），跟业务无关，所有项目可直接采用。如项目有不同约定（如 `docs/prds/`、`docs/requirements/`），在 role / CLAUDE.md 中 override 即可。

### Step 4: 按 §7 模板生成 PRD

读取下方 **§7 PRD 模板**（本文件内），按模板写 PRD，**两部分一气呵成**：

- **第一部分「需求设计」** 面向项目经理 / 业务方（自然语言，业务可见行为）
- **第二部分「系统设计」** 面向开发人员（表结构 / API / 业务规则，直接可用）

**写作质量要求 8 条**：见 §8。

### Step 5: 输出文件

**默认路径**：`docs/stories/<NN>-<name>/prd.md`

- 命名规则见 Step 3
- 若 `docs/stories/<NN>-<name>/` 目录不存在，先创建

**项目可在 role / CLAUDE.md 中 override**（如改用 `docs/prds/` 或 `docs/requirements/`）：本 skill 优先读项目约定，没有约定才走 `docs/stories/` 默认。

**禁止动作**：

- ❌ 推送到 GitHub/GitLab/Linear issue tracker
- ❌ 写到 skill 自身的默认路径（如 `docs/superpowers/prds/`），除非项目明确允许
- ❌ 触发任何外部 API 调用

### Step 6: 汇报 + 等用户审

完成后输出一条简报：

```
PRD 已写入 <实际输出路径>
  - <N> 张表 / <M> 个 API / <K> 条 AC
  - 流程图占位:diagrams/state-machine.svg / sequence.svg / er-diagram.svg

下一步:用户 review prd.md。
  通过 → 后续阶段（如画图、拆任务等）
  不通过 → 回 brainstorming/grill-me 重谈
```

**不要主动推进到下一阶段**。

原因：PRD 评审是用户的关键审阅点，提前推进会让用户失去 review 机会，万一 PRD 有偏差会导致后续工作返工。最稳的做法是：写完 PRD → 输出简报 → 停下 → 等用户明确「通过」或「继续」。

---

## 4. 关键原则

- **合成模式**：你已经知道一切。不要问，只要写。
- **Deep Module**：找封装功能多的核心模块，不要扁平铺。
- **复用既有命名**：从项目文档术语词汇表取，新字段才命名。
- **AC 必须可机器执行**：角色 + 操作 + 数据状态，三要素齐全（具体测试工具由项目选 —— Playwright / Cypress / agent-browser 等）。
- **本地化产物**：不推 issue tracker，只写本地文件。

---

## 5. 与其他 skill 的关系

```
/brainstorming（发散）
   ↓
/grill-me（收敛）
   ↓
/synthesize-prd  ← 本 skill
   ↓
   ═══ 用户审 PRD ═══
   ↓
/baoyu-diagram（画图，给 PRD 内的占位补 SVG）
```

**前置依赖**：`/brainstorming` + `/grill-me` 必须先跑完，对话上下文里要有充分的决策沉淀。

**后置触发**：用户确认后由用户决定下一步（画图 / 拆任务 / 评审 / 开发等），本 skill **不主动调任何下游 skill**。

---

## 6. 项目级 override

不同项目对 PRD 输出格式 / 路径 / 模板内容可能有不同约定。建议项目通过以下方式 override 本 skill 的默认行为：

1. **在 `.claude/roles/<role>.md` 或 `CLAUDE.md` 中声明项目特定约束**，例如：
   - 输出路径（如本 skill 默认 `docs/stories/<NN>-<name>/`，项目可改 `docs/prds/<NN>-<name>/`）
   - 项目特定模板片段（如补充 iron-flow-scf 项目的「讲解模式 + 关停 Mock」AC 类）
   - 项目特定的 AC 测试工具（agent-browser / Playwright / Cypress 等）
2. **本 skill 默认读 role 文件的约束**，project context 优先级高于本 skill 内的默认值

---

## 7. PRD 模板

> 执行 Step 4 时复制本节内容到 `docs/stories/<NN>-<name>/prd.md`（项目可在 role / CLAUDE.md 中 override 路径），按本次需求填空。

```markdown
# [Stage N] <流程名> · 产品需求文档（PRD）

> **状态**：YYYY-MM-DD ↔ 待定
> **Plan**：[./plan.md](./plan.md) — 技术任务拆分（如有后续阶段）
> **Roadmap**：参见项目 roadmap（如有）

---

# 第一部分：需求设计

> 面向项目经理 · 自然语言 · 业务可见行为

## 1. 概述

- **Problem**：这个阶段要解决什么业务问题
- **Users**：涉及哪些角色（项目角色定义见项目顶层文档）
- **一句话定位**：解决 X 的 Y 能力

## 2. 范围

**范围内**：
- ...

**范围外**（明确不做，归后续阶段或不实现）：
- ❌ xxx — 归后续阶段
- ❌ xxx — 不在本系统处理

## 3. 业务背景

说明本模块在业务链中的定位，解决什么问题，依赖哪些上游模块，为哪些下游模块提供数据基础。

## 4. 角色与入口

| 角色 | 所在系统 | 操作入口 | 主要职责 |
|------|---------|---------|---------|
| <角色 A> | <系统名> | <菜单 / 页面> | <职责> |
| <角色 B> | <系统名> | <菜单 / 页面> | <职责> |

## 5. 业务流程

### 5.1 主流程（逐步表）

| 步 | 角色 | 触发动作 | 产出 / 状态变更 | 后端动作 |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

### 5.2 异常分支

每条异常分支说明：触发节点 / 操作角色 / UI 交互 / 状态变更 / 后续走向。

- **拒绝**：触发节点 xxx，状态变更到 rejected，终态不可激活
- **撤回**：...
- **补充资料**：...

### 5.3 流程图

> 由独立的图表生成 skill（如 `/baoyu-diagram`）在 PRD 审过后生成；本处先留占位。

![状态流转](diagrams/state-machine.svg)
![跨角色时序](diagrams/sequence.svg)
![用户路径](diagrams/user-journey.svg)

## 6. 状态流转（如有状态机）

> 无状态机的简单需求可删除本节。

| 状态值 | 显示名称 | 含义 | 进入条件 | 可执行操作 |
|--------|---------|------|---------|----------|
| pendingSubmit | 待提交 | 草稿 | 初次录入保存 | 继续编辑、提交 |
| ... | ... | ... | ... | ... |

> 说明关键约束：是否存在终态、是否允许回退等。

## 7. 用户故事

> **覆盖所有角色 × 所有典型操作路径 × 所有业务价值视角**。用户故事是 PRD 评审时业务方直接对照需求的部分，**详尽程度看需求自然铺**，不强求数量，避免凑数灌水。

**示例 — 简单需求（1-3 条）**：
- As 用户, I want to 改密码, so that 账号安全

**示例 — 中等需求（5-8 条）**：
- As 业务员, I want to 录入授信申请, so that 启动业务
- As 风控员, I want to 审核申请, so that 控制风险
- As 法务, I want to 出合同, so that 签约合规
- As 企业, I want to 电签合同, so that 签约高效
- As 业务员, I want to 终止申请, so that 处理异常

**复杂需求（10+ 条）**：按角色 × 操作路径自然铺，本文不举完整例。

**按本次需求实际填写**：
- As **<角色>**, I want to <操作路径>, so that <业务价值>
- As **<角色>**, ...

## 8. 验收标准（Acceptance Criteria）

> 验证阶段逐条跑的依据。每条须包含：**角色 + 操作路径 + 结果状态** 三要素，具体到「点哪个按钮 / 跳哪个页面 / DB 数据变成什么」。
>
> **核心原则**（来自 mattpocock/to-prd）：测**外部可见行为**（用户看得到 / DB 状态可观测），**不测实现细节**（不依赖具体函数名 / 类结构 / 内部状态）—— 实现可重构，AC 应保持绿。
>
> 具体测试工具由项目选（Playwright / Cypress / agent-browser 等），AC 描述方式与工具无关。

**坏 / 好 AC 对照示例**：
```
❌ 坏 AC(测实现细节,重构就挂):
"QuotaApplyService.submit() 函数返回 status=200"

✅ 好 AC(测外部可见行为,实现演进保持绿):
"业务员点提交按钮后,列表页出现新记录,状态='待审核',
 LocalStorage iron_flow_quota_apply 多 1 条记录"
```

### 主流程闭环

- [ ] **AC1 <简短名>**：<角色> 进 <系统> <菜单>，执行 <操作>，结果：<页面变化> + <DB 状态变更>
- [ ] **AC2**：...

### 异常分支

- [ ] **ACn <简短名>**：...

### 权限验证（如有权限模型）

- [ ] **ACn <角色> 菜单权限**：用 <role> 测试账号登录 <系统>，<可见 / 不可见> 哪些菜单 + 按钮

---

# 第二部分：系统设计

> 面向开发人员 · 表结构 / API / 规则直接可用 · 不写演进史，只写"该怎么做"

## 9. 数据模型

> 用 MySQL DDL 直接展示，开发可直接拿去建表。表间关联关系见下方文字说明；ER 图占位：[./diagrams/er-diagram.svg](./diagrams/er-diagram.svg)
>
> **关联约束策略**：本项目不设 `FOREIGN KEY` 强制外键约束（避免跨服务/微服务边界耦合 + 写入性能下降 + 删除级联误伤）。关联字段加索引加速查询，关联一致性由业务层保证。

### 9.x <表名>（中文用途）

**用途**：一句话说明这张表存什么数据，与哪些表关联。

```sql
CREATE TABLE `<resource>` (
  `id`           VARCHAR(36)     NOT NULL                COMMENT '主键 (UUID)',
  `name`         VARCHAR(50)     NOT NULL                COMMENT '名称',
  `status`       VARCHAR(32)     NOT NULL                COMMENT '状态枚举 (见 §10 XxxStatus)',
  `related_id`   VARCHAR(36)     NOT NULL                COMMENT '业务关联 <other_table>.id (不设 FK,业务层保证一致性)',
  `amount`       DECIMAL(15,2)   DEFAULT NULL            COMMENT '金额',
  `created_at`   BIGINT          NOT NULL                COMMENT '创建时间 (epoch ms)',
  `created_by`   VARCHAR(36)     NOT NULL                COMMENT '创建人 ID',
  `updated_at`   BIGINT          NOT NULL                COMMENT '更新时间 (epoch ms)',
  `updated_by`   VARCHAR(36)     NOT NULL                COMMENT '更新人 ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)                          COMMENT '名称唯一约束',
  KEY `idx_status_created_at` (`status`, `created_at`)   COMMENT '按状态 + 时间倒序查询 (列表页常用)',
  KEY `idx_related_id` (`related_id`)                    COMMENT '关联 <other_table>.id 查询加速 (替代 FK)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4                  COMMENT='<表的中文用途一句话>';
```

> **Seed**（开发用默认数据）：N 条，含 ...

**DDL 编写要点**：
- 字段全部 `NOT NULL`，可选字段用 `DEFAULT NULL` 显式标注
- 时间戳用 `BIGINT` 存 epoch ms（跨时区无歧义）
- UUID 主键用 `VARCHAR(36)`；自增 ID 用 `BIGINT UNSIGNED`
- 枚举字段用 `VARCHAR(32)` + COMMENT 指向 §10 类型定义（避免 MySQL ENUM 扩展难）
- 金额用 `DECIMAL(p,s)`，禁用 `FLOAT/DOUBLE`
- 索引命名：唯一 `uk_<col>`，普通 `idx_<col1>_<col2>`，且**每个索引必须有 COMMENT 说明用途**
- 每个字段、每个索引、每张表都有 COMMENT
- 不写 `FOREIGN KEY`，但在关联字段的 COMMENT 和 `idx_<col>` COMMENT 里明确说明业务关联关系

### 9.y 表间关联关系

> DDL 里没有 FK 强约束，靠下方文字说明 + 业务层校验维护数据一致性。

- `<表A>.<fieldB>` 业务关联 `<表B>.id`（含义：xxx；`idx_<fieldB>` 加速查询；删除 `<表B>` 时业务层级联清理 `<表A>`）
- `<表C>` 是 `<表A>` 与 `<表B>` 的 M:N 关联表（含 `idx_a_id` 和 `idx_b_id` 双向查询）

## 10. 枚举与类型定义

> 用项目主语言定义（TypeScript / Go / Java / Python 等都可，下例为 TypeScript）。

```ts
// 本阶段新增枚举，命名风格按项目约定（下例为 camelCase）
export type XxxStatus = 'draft' | 'submitted' | 'approved' | 'rejected';

export type XxxNode =
  | 'stepA'   // 步骤A含义
  | 'stepB'   // 步骤B含义
  | 'stepC';  // 步骤C含义

export type XxxType = 'typeA' | 'typeB';
// 复用已有枚举（不新增）：XxxExisting — 已存在
```

## 11. 核心业务规则

> 影响系统行为的关键规则，开发和测试对齐依据，每条一行。

- **规则 1**：xxx 条件下，系统执行 xxx；违反时返回 4xx + 错误码
- **规则 2**：<字段名> 唯一性约束，冲突时返回 409 + message「xxx」
- **规则 3**：<操作> 需满足 currentNode ∈ {stepA, stepB}，否则返回 403
- **规则 4**：<状态机约束>：approved / rejected 为终态，不允许任何 PATCH 操作

## 12. API 设计

> 每个 endpoint 注明：方法 + URL + 入参摘要 + 权限点（如有权限模型）。

```
# <资源名>（中文）
POST   /api/<resource>                   创建；权限：<权限点>
GET    /api/<resource>                   列表；?status=&keyword=&<filter>=；权限：<权限点>
GET    /api/<resource>/:id               详情；权限：<权限点>
PATCH  /api/<resource>/:id               编辑；权限：<权限点>
PATCH  /api/<resource>/:id/<action>      状态转换（含义：xxx）；权限：<权限点>
DELETE /api/<resource>/:id               删除；权限：<权限点>
```

> 如项目有权限框架，handler 入口须做权限校验（fail-close）。权限点格式按项目约定。

### 关键算法

- **<算法名>**：handler 如何实现（如异步定时 / 自动计算 / 级联写入）—— 可用伪代码描述（见 §2.3 例外 2）

## 13. 后端实现结构（项目相关，可选）

> 不同项目的代码组织约定不同（Mock-based 前端原型 / Spring Boot 后端 / Express handler / FastAPI router 等），按项目实际填写或删除本节。

```
<项目实际的目录结构>
  <模型层>/
    <resource>.<ext>        # 主资源
    <resource2>.<ext>       # 关联资源
  <handler 层>/
    <resource>.<ext>        # 处理本资源所有接口
  <注册入口>                # 注册新资源/handler
```

## 14. 权限设计（涉及新权限点时填写）

| 权限点 | 含义 | 适用角色 | 现状 |
|--------|------|---------|------|
| `<权限点格式按项目约定>` | xxx | 角色名 | 新增 / 已有 |

## 15. 依赖

- 上游阶段产出：`docs/stories/<上游 NN>-<name>/`（如有）
- 业务源：<项目业务参考文档章节>
- 架构基线：<项目架构 / 命名 / 工程约束文档>
- 命名空间约束：表名 / API / 字段 严格用项目通用术语，**不引用外部系统项目代号**
```

---

## 8. 写作质量要求

合成 PRD 时严格遵守以下 8 条：

1. 每张表用 **MySQL DDL** 完整展示（`CREATE TABLE ... ENGINE=InnoDB`，开发可直接执行建表）；字段、索引、表三层都必须有 `COMMENT`
2. **不写 `FOREIGN KEY` 强约束**（避免跨服务耦合 / 写入降速 / 删除级联误伤）；关联字段改用 `KEY idx_<col>` 索引加速 + COMMENT 写明业务关联关系；一致性由业务层保证
3. 索引命名：唯一 `uk_<col>`，普通 `idx_<col1>_<col2>`，**每个索引必须有 COMMENT 说明用途**
4. 字段类型规范：UUID 主键用 `VARCHAR(36)`、时间戳用 `BIGINT` (epoch ms)、金额用 `DECIMAL(p,s)`（禁 FLOAT/DOUBLE）、枚举字段用 `VARCHAR(32)` + COMMENT 指向 §10 类型定义
5. 枚举值用语言无关的代码块定义（TypeScript / Go / Java 等）
6. 表间关联用文字逐条说明（§9.y）+ 在「业务流程」section 留 ER 图占位（`diagrams/er-diagram.svg`）
7. API 每条注明 endpoint + 入参摘要 + 权限点（如有权限模型）
8. AC（验收标准）**必须可机器执行**：包含**角色 / 操作路径 / 结果状态**三要素，具体到「点哪个按钮 / 跳哪个页面 / DB 数据变成什么」

---

## 9. 模板使用注意

1. **占位符替换**：所有 `<xxx>` 是占位符，根据本次需求填实际内容
2. **章节按需删减**：
   - §6 状态流转：无状态机的简单需求可删
   - §13 后端实现结构：纯前端无关后端的需求可删
   - §14 权限设计：无新权限点可删
3. **AC 数量参考**：简单需求 5-8 条，中等需求 10-15 条，复杂需求 20+ 条
4. **数据模型表数量**：简单需求 1-2 张表，中等 3-5 张，复杂 6+ 张
5. **项目级 override**：如项目有自定义 PRD 模板（如 iron-flow-scf 的两段式 + 讲解模式 AC），优先用项目模板覆盖本通用模板

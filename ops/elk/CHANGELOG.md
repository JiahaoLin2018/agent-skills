# CHANGELOG — elk

## 2026-03-13: 全面优化 — 内容精简与结构拆分

**架构优化**

- `SKILL.md`: 精简配置加载流程章节（34 行 → 3 行概要），补充 Python 3 依赖说明，改写 description 增强触发场景覆盖
- `actions/query.md`: 报告格式模板（阶段三/四/五，约 110 行）拆分到 `references/report-format.md`，统一配置加载写法
- `actions/help.md`: 统一配置加载写法，与 ping/indices/config 保持一致
- `references/report-format.md`: 新建，承接查询报告的汇报头、日志明细、分析报告格式规范
- `README.md`: 目录结构树补充 `references/` 目录

## 2026-03-12: 模板配置优化 — 密码隐藏与参数说明

**文档完善**

- `templates/skill_config_elk-template.yml`: 密码替换为占位符，添加参数详细注释，标注日志库属性，引导用户获取正确 ES 地址，精简为单个示例项目
- `features.md`: 配置说明补充参数详解表、ES 地址获取指引、日志库与业务数据库区分说明

## 2026-03-10: 配置项自动检测

**新功能**

- `SKILL.md`: 新增"配置加载流程"章节，配置文件不存在时自动从模板创建，projects 为空时提示使用 `/elk indices` 发现可用索引
- `actions/query.md`: 步骤 1.1 配置加载引用自动检测流程
- `actions/help.md`、`actions/ping.md`、`actions/indices.md`、`actions/config.md`: 统一增加配置加载自动检测步骤

## 2026-03-10: 合规修复 — 配置命名规范和 query action 章节结构

**文档完善**

- `SKILL.md`: 配置文件命名规范从固定 `.sh` 后缀改为 `.<ext>`，适配 elk 实际使用的 `.yml` 格式
- `actions/query.md`: 补充标准 `## 命令格式` 和 `## 步骤` 章节头

## 2026-03-10: 优化查询策略 — 新增时间边界探测和随机抽样

**健壮性改进**

- `actions/query.md`: 新增 2.0.1 时间边界探测步骤，宽时间范围查询（≥4h）前先并行取最早/最新记录确定数据实际窗口，避免盲目猜测时间段导致空查询
- `actions/query.md`: 新增 2.4.1 随机抽样策略，使用 ES `function_score` + `random_score` 实现真随机抽样，附降级方案
- `actions/query.md`: 阶段二开头新增并行调用指导表，标明可并行和必须串行的查询步骤依赖关系

## 2026-03-10: SKILL.md 合规结构优化

**架构优化**

- `SKILL.md`: 重构为标准章节结构（`<skill_dir>` 引用块 → 文档职责说明 → 配置 → 用法 → Actions → 执行流程 → 重要说明），移除面向人的示例内容
- `install.sh`: 移除硬编码 SKILL_NAME，改为从目录名自动推导
- `actions/*.md`: 补充命令格式章节，规范步骤编号和加粗格式

## 2026-03-10: 配置文件结构合规性优化

**文档完善**

- `features.md`: 按 skill_kit 模板规范重排章节顺序（安装教程 → 配置说明 → 功能介绍 → 使用示例），修复安装路径 `elk_analyzer` → `elk`，补充目录结构小节
- `CHANGELOG.md`: 修正标题名称 `elk_analyzer` → `elk`

## 2026-03-10: 配置文件命名规范化

**架构优化**

- 配置文件从 `elk-config.yml` 重命名为 `skill_config_elk.yml`，符合 skill_kit 统一命名规范 `skill_config_<技能包名>.yml`
- 模板文件从 `elk-config-template.yml` 重命名为 `skill_config_elk-template.yml`
- 全部引用文件同步更新：`SKILL.md`、`actions/*.md`、`scripts/elk_api.py`、`features.md`、`install.sh`

## 2026-03-10: 按 skill_kit 标准规范优化目录结构

**架构优化**

- `SKILL.md`: 从 `skill/` 子目录移到根目录
- `actions/`: 从 `skill/actions/` 移到根目录
- `install.sh`: 替换为通用安装脚本（覆盖 `SKILL_NAME="elk"`）
- `features.md`: 补充安装后配置步骤（配置文件复制、chmod、Python 检查）
- 删除 `skill/` 嵌套目录

## 2026-03-06

### 结构规范化
- `install.sh`：修复 SKILL.md 安装路径（`skill/SKILL.md` → `SKILL.md`），符合最新标准
- `install.sh`：移除错误创建的 `skill/` 子目录，新增安装 `templates/`、`actions/` 目录
- `skill/SKILL.md`：重构为精简调度器，补全 frontmatter（`argument-hint`、`disable-model-invocation: true`）
- 新增 `skill/actions/` 目录，抽出 5 个 action 文件：`query.md`、`help.md`、`indices.md`、`ping.md`、`config.md`
- 新增本文件 `CHANGELOG.md`

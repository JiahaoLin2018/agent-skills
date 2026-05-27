# agent-skills

> 🛠 **Personal Claude Code skill workshop** — `lab` 端,在这里造 skill;成熟后由 [`ai-skill-hub`](https://github.com/JiahaoLin2018/ai-skill-hub) 收录、分类、推荐。

按角色场景组织的个人 Claude Code Skill 集合,可直接安装到 `~/.claude/skills/`。

```
🏭 hub  ai-skill-hub        — 浏览/检索站点(VitePress 文档)
🔬 lab  agent-skills (这里)  — 自造 skill 的源码仓库
```

## 收录索引

| Skill | 分类 | 子类 | 用途 | 状态 |
|-------|------|------|------|------|
| [tt-statusline](./general/tt-statusline/) | general | token 追踪 | Claude Code 状态栏实时显示 token 占用、速率限制、费用等（配置打包，非 slash command） | ✅ |
| [token-tracker](./general/token-tracker/) | general | token 追踪 | `tt daily/weekly/sessions` 等命令查看历史 token 用量与费用报告（pip 包） | ✅ |
| [synthesize-prd](./product/synthesize-prd/) | product | PRD 文档 | brainstorming+grill-me 后合成结构化 PRD（双段式 + MySQL DDL + AC），**不推 issue tracker**，mattpocock/to-prd 的本地化替代 | ✅ |
| [elk](./ops/elk/) | ops | 监控排查 | 自然语言查 ES 日志、traceId 关联追踪、AI 根因诊断 | ✅ |
| [setup-transfer-clash](./ops/setup-transfer-clash/) | ops | 网络代理 | 一键部署 VPS 代理节点(3x-ui + BBR + 订阅转换) | ✅ |

> 📌 后续按 `general / product / frontend / backend / ops` 五大类逐步补充。

## 安装方式

每个 skill 都可独立安装,有两种方式:

### 方式 1:直接 clone + 软链(推荐)

```bash
git clone git@github.com:JiahaoLin2018/agent-skills.git ~/agent-skills
ln -s ~/agent-skills/ops/elk ~/.claude/skills/elk
ln -s ~/agent-skills/ops/setup-transfer-clash ~/.claude/skills/setup-transfer-clash
```

更新时只需 `cd ~/agent-skills && git pull`,所有软链 skill 同步更新。

### 方式 2:使用 install.sh（部分 skill 提供）

部分 skill 内置 `install.sh`,会把目录复制到 `~/.claude/skills/<skill-name>/`:

```bash
cd ops/elk && bash install.sh
cd ops/setup-transfer-clash && bash install.sh
```

> ⚠️ 复制式安装升级需要重新执行,推荐方式 1。
>
> **single-file skill**（如 `product/synthesize-prd`）只有一个 `SKILL.md`,**没有 `install.sh`**,只能用方式 1 软链或手动 `cp`。

## 目录结构

```
agent-skills/
├── README.md           # 本文件 — 总索引
├── LICENSE             # MIT
├── general/            # 跨场景通用 skill (思维流程、skill 管理)
├── product/            # 产品经理工作流 (PRD / 流程图 / 演示)
├── frontend/           # 前端开发与设计 (UI / React / 视频)
├── backend/            # 服务端 (暂未收录)
└── ops/                # 运维 (监控 / 网络代理 / CI/CD)
    ├── elk/
    └── setup-transfer-clash/
```

每个 skill 子目录的标准结构:

```
<skill-name>/
├── SKILL.md          # Claude 读取的指令文件
├── README.md         # 人读的入门指引(安装/配置/示例)
├── CHANGELOG.md      # 变更日志
├── install.sh        # 安装到 ~/.claude/skills/
├── actions/          # 各 action 详细步骤(可选)
├── scripts/          # 辅助脚本(Python/Shell)
├── templates/        # 配置模板(可选)
├── references/       # 参考文档(可选)
└── evals/            # 触发 eval 测试用例(可选)
```

## 与 ai-skill-hub 的关系

| | agent-skills (这里) | ai-skill-hub |
|---|--------------------|--------------|
| 角色 | 🔬 lab — skill 源码 | 🏭 hub — skill 收录展示 |
| 形态 | 代码仓库 | VitePress 站点 |
| 内容 | 自造 skill | 自造 + 三方 skill 索引 |
| 安装 | git clone / install.sh | 仅展示,不直接安装 |

发现新的好用 skill?去 [ai-skill-hub Issues](https://github.com/JiahaoLin2018/ai-skill-hub/issues) 提建议。

## Contributors

<table>
<tr>
<td align="center" width="160">
<a href="https://github.com/JiahaoLin2018">
<img src="https://github.com/JiahaoLin2018.png" width="80" alt="JiahaoLin2018" /><br/>
<b>JiahaoLin2018</b>
</a><br/>
<sub>skill 开发 · workshop 维护</sub>
</td>
<td align="center" width="160">
<a href="https://claude.com/claude-code">
<img src="https://github.com/anthropics.png" width="80" alt="Claude Code" /><br/>
<b>Claude Code</b>
</a><br/>
<sub>skill 调研 · 文档优化</sub>
</td>
</tr>
</table>

> Claude 通过 commits 中的 `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` trailer 协作参与。

## License

MIT — 详见 [LICENSE](./LICENSE)。

各 skill 内的第三方依赖与法律声明以其 SKILL.md / README.md 顶部为准。

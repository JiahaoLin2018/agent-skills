# setup-transfer-clash — 更新日志

## 2026-03-27: 终极配置模板 — 无视数据库版本、永不报错

**重大更新**

- `scripts/sub_server.py`:
  - 配置模板全面重构：Fake-IP + Sniffer + AI隔离 + 自动测速
  - DNS nameserver-policy 改为纯域名后缀，零依赖 geosite 数据库
  - Rules 移除所有不稳定的 geosite 分类（google/github/telegram/apple/gfw）
  - AI 服务规则全部使用 DOMAIN-SUFFIX，永不报错
  - 节点名称自动包含用户邮箱
  - PROFILE_NAME 显示为 `Buddy.home (邮箱)`
  - 随机端口范围改为 10000-65535
- `scripts/full_deploy.py`:
  - 交互式输入 SSH 信息，无需配置文件
  - 移除 references 目录依赖
- `actions/init.md`: 删除，合并到 deploy.md
- `actions/deploy.md`: 更新为完整的部署说明
- `SKILL.md` / `README.md`: 全面更新，突出零报错特点

**配置特点**

| 特点 | 说明 |
|------|------|
| **零报错** | AI 规则用域名后缀，不依赖 geosite 数据库 |
| **高通用性** | 国内走国内，AI 走隔离，其他全部走代理 |
| **无视伪装** | 无论 Reality SNI 伪装成什么，自动落入 MATCH |

---

## 2026-03-27: 一键部署 + 随机端口 + 多线程优化

**重大更新**

- `scripts/full_deploy.py`: 新增一键全流程部署脚本，自动完成 3x-ui 安装 + BBR 开启 + 订阅服务部署
- `scripts/sub_server.py`:
  - `HTTPServer` → `ThreadingHTTPServer`，支持多线程并发
  - 新增 `setup()` 方法设置连接超时（默认 10s）
  - 新增 `handle_one_request()` 异常捕获，防止恶意扫描阻塞
  - 新增 `do_GET()` 异常处理
  - 新增 `REQUEST_TIMEOUT` 配置项
- `scripts/deploy_sub_server.py`: 新增随机端口功能（20000-50000），自动检测公网 IP
- `actions/init.md`: 重写为一键部署流程，调用 `full_deploy.py`
- `actions/deploy.md`: 更新为仅部署订阅服务
- `actions/status.md`: 更新状态检查脚本
- `references/skill_config_*.conf`: `SUB_PORT` 改为可选，不填自动随机生成
- `SKILL.md` / `README.md`: 全面更新文档

**安全性提升**

- 随机端口避免扫描
- 多线程防止服务阻塞
- 超时机制防止恶意连接

---

## 2026-03-26: 新增 init action — 安装 3x-ui + 开启 BBR

**新功能**

- `actions/init.md`: 新增，全新 VPS 环境初始化步骤：检测并安装 3x-ui 面板（官方 MHSanaei/3x-ui）、开启 BBR 拥塞控制、验证环境并引导后续步骤
- `SKILL.md`: 更新 frontmatter description 和 argument-hint，新增推荐使用顺序（init → deploy → status），补充 init 相关重要说明
- `README.md`: 全面更新，新增 init 功能介绍、推荐使用顺序流程图、init 使用示例；修正目录结构（移除旧 config.conf 引用）

---

## 2026-03-26: 修复 status action 硬编码凭据问题

**安全修复**

- `actions/status.md`: 移除硬编码的 VPS_HOST / VPS_PASSWORD，改为在运行时从 `~/.claude/skill_config_setup-transfer-clash.conf` 读取，与 deploy action 保持一致
- `actions/status.md`: 端口从硬编码 `3000` 改为读取配置中的 `SUB_PORT`
- `actions/status.md`: 异常处理表格移除已删除的 `update` action 引用
- `actions/deploy.md`: 脚本路径从项目相对路径改为 `~/.claude/skills/setup-transfer-clash/scripts/deploy_sub_server.py`，适配安装后的标准路径

---

## 2026-03-26: 遵循 skill-kit 配置文件命名规范

**规范对齐**

- `references/skill_config_setup-transfer-clash.conf`: 新增，替换原 `references/config.conf.template`，遵循 skill-kit 命名规范 `skill_config_<name>.conf`
- `references/config.conf.template`: 删除，由上方文件替代
- `scripts/deploy_sub_server.py`: 更新 `CONFIG_FILE` 路径为 `~/.claude/skill_config_setup-transfer-clash.conf`
- `actions/deploy.md`: 更新 Step 1，引用新配置路径
- `SKILL.md` / `README.md`: 同步更新配置初始化命令

---

## 2026-03-26: 移除 update action，配置模板移至 references/

**架构优化**

- `actions/update.md`: 删除，部署即重新发布，不需要独立 update action
- `references/config.conf.template`: 新增，配置模板从 `scripts/` 移至 `references/`，职责分离更清晰
- `scripts/deploy_sub_server.py`: 更新配置模板路径提示
- `SKILL.md` / `README.md`: 同步移除 update 相关内容，更新模板路径引用

---

## 2026-03-26: 敏感信息移入独立配置文件

**安全改进**

- `scripts/config.conf.template`: 新增配置模板，包含 VPS_HOST/VPS_PASSWORD/SERVER_IP 等所有敏感字段
- `scripts/deploy_sub_server.py`: 移除硬编码的 SERVER_CONFIG，改为从 `config.conf` 读取；新增配置校验，未填写时给出明确提示
- `scripts/sub_server.py`: 移除硬编码的 CONFIG 字典，改为从 `/opt/sub-server/config.conf` 读取；deploy 时自动生成服务器端配置（不含 SSH 密码）
- `SKILL.md`: 更新配置说明，标注 config.conf 不可提交
- `README.md`: 新增配置项说明表格，补充 config.conf 初始化步骤

---

## 2026-03-26: 按 skill-kit 规范重构目录结构

**架构优化**

- `SKILL.md`: 新增，从单文件 md 拆分为标准 skill 目录结构，含 frontmatter 和执行流程
- `actions/deploy.md`: 新增，首次部署步骤独立文档
- `actions/update.md`: 新增，脚本更新流程独立文档
- `actions/status.md`: 新增，状态检查流程独立文档
- `README.md`: 新增，面向用户的入门指引
- `install.sh`: 新增，通用安装脚本
- `scripts/sub_server.py`: 从根目录移入 scripts/

---

## 2026-03-26: 修复 Clash Verge 订阅名显示问题

**Bug 修复**

- `scripts/sub_server.py`: `Content-Disposition` filename 去掉引号（`filename=Buddy.home`），修复 Clash Verge 将引号也显示在订阅名中的问题

---

## 2026-03-26: 端口从 3001 改为 3000

**架构优化**

- `scripts/sub_server.py`: `CONFIG.port` 由 3001 改为 3000
- `scripts/deploy_sub_server.py`: `SERVICE_PORT` 由 3001 改为 3000，同步更新 iptables 规则

---

## 2026-03-26: 初始版本部署

**新功能**

- `scripts/sub_server.py`: 初始版本，实时读取 3x-ui SQLite，生成 Clash Meta YAML，通过 subId 动态查询用户，无需维护用户列表
- `scripts/deploy_sub_server.py`: 一键部署脚本，通过 paramiko SSH 完成上传、systemd 注册、防火墙配置、启动验证

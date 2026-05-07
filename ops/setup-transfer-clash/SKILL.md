---
name: setup-transfer-clash
description: 一键部署 VPS 代理节点：安装 3x-ui + 开启 BBR + 部署 VLESS-Reality 订阅转换服务。支持全流程自动化，随机端口防扫描，内置速率限制防滥用。当用户需要初始化 VPS、部署订阅服务、检查服务状态时使用此 skill。
argument-hint: "deploy | status"
disable-model-invocation: true
---

# setup-transfer-clash — 一键 VPS 代理节点部署

> ⚠️ **法律声明**：本 Skill 仅供学习和研究目的使用。用户应遵守当地法律法规;对于用户违反当地法律的行为，开发者概不负责。

## 快速开始

```
/setup-transfer-clash deploy   # 全流程部署：3x-ui + BBR + 订阅服务
/setup-transfer-clash status   # 检查服务运行状态
```

## 脚本文件

- `scripts/full_deploy.py` — 一键部署脚本（执行时提示输入 SSH 信息）
- `scripts/sub_server.py` — VPS 端订阅服务

## 功能特点

- **交互式输入**：执行时提示输入 SSH 连接信息，无需配置文件
- **随机端口**：订阅服务端口随机生成（10000-65535），避免扫描
- **速率限制**：每个 IP 每分钟最多 10 次请求，防止滥用
- **安全校验**：subId 格式校验，防止路径遍历攻击
- **代理支持**：自动识别 X-Real-IP / X-Forwarded-For，适配 Nginx 反代
- **极简配置模板**：无视数据库版本、无视伪装域名、永不报错
  - Fake-IP 模式：秒开网页
  - Sniffer 嗅探：识别 App 内部流量
  - AI 服务硬绑定：保持 Claude/GPT 等 AI 服务连接稳定
  - P2P 流量直连优化：避免 VPS 转发大流量影响主线路
  - DNS 防泄漏：nameserver-policy 智能分流

## 配置特点

| 特点 | 说明 |
|------|------|
| **零报错** | AI 规则使用域名后缀，不依赖 geosite 数据库 |
| **高通用性** | 国内走国内，AI 走节点，其他全部走代理 |
| **无视伪装** | 无论 Reality SNI 伪装成什么，自动落入 MATCH |
| **单节点优化** | 一次 SQL 查询完成订阅生成，高效简洁 |

## 配置文件 (config.conf)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| SERVER_IP | - | 服务器公网 IP |
| SUB_PORT | 随机 | 订阅服务端口 (10000-65535) |
| DB_PATH | /etc/x-ui/x-ui.db | 3x-ui 数据库路径 |
| LOG_FILE | /opt/sub-server/sub.log | 日志文件路径 |
| REQUEST_TIMEOUT | 10 | 请求超时时间（秒） |
| RATE_LIMIT | 10 | 每个 IP 窗口内最大请求数 |
| RATE_WINDOW | 60 | 速率限制窗口（秒） |

## 管理命令

```bash
systemctl status sub-server      # 查看状态
systemctl restart sub-server     # 重启服务
journalctl -u sub-server -f      # 查看日志
```

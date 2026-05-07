# setup-transfer-clash — 一键 VPS 代理节点部署

> ⚠️ **法律声明**：本 Skill 仅供学习和研究目的使用。用户应遵守当地法律法规;对于用户违反当地法律的行为，开发者概不负责。

一键部署 VPS 代理节点：安装 3x-ui + 开启 BBR + 部署 VLESS-Reality 订阅转换服务。支持随机端口防扫描，配置模板无视数据库版本永不报错。

## 安装

```bash
# 安装 skill
bash vpn_server/skills/setup-transfer-clash/install.sh

# 安装依赖
pip install paramiko
```

## 使用

### 一键部署

```
/setup-transfer-clash deploy
```

脚本会提示输入 SSH 连接信息：
- 服务器 IP（必填）
- SSH 端口（默认 22）
- 用户名（默认 root）
- 密码（必填）

自动完成：
1. 安装 3x-ui 面板
2. 开启 BBR 加速
3. 部署订阅服务（随机端口 10000-65535）
4. 输出部署报告

### 检查状态

```
/setup-transfer-clash status
```

## 目录结构

```
setup-transfer-clash/
├── SKILL.md              # Skill 主文件
├── actions/
│   ├── deploy.md         # 一键部署
│   └── status.md         # 状态检查
├── scripts/
│   ├── full_deploy.py    # 一键部署脚本
│   └── sub_server.py     # VPS 端订阅服务
└── install.sh            # 安装脚本
```

## 功能特点

| 特点 | 说明 |
|------|------|
| **一键部署** | 交互式输入 SSH 信息，自动完成全部安装 |
| **随机端口** | 10000-65535 随机端口，避免扫描 |
| **速率限制** | 每个 IP 每分钟最多 10 次请求，防止滥用 |
| **安全校验** | subId 格式校验，防止路径遍历攻击 |
| **代理支持** | 自动识别 X-Real-IP / X-Forwarded-For |
| **零报错配置** | AI 规则用域名后缀，不依赖 geosite 数据库 |
| **Fake-IP** | 秒开网页，198.18.0.1/16 假 IP 池 |
| **Sniffer** | 识别 App 内部不走 DNS 的流量 |
| **AI 硬绑定** | OpenAI/Claude/Gemini 强制走节点，保持连接稳定 |
| **P2P 保护** | 强制 P2P 下载直连，避免占用 VPS 带宽 |
| **DNS 防泄漏** | nameserver-policy 智能分流 |

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

## 配置模板特点

### 无视数据库版本
- AI 服务规则使用 `DOMAIN-SUFFIX` 域名后缀匹配
- 不依赖 `geosite:openai`、`geosite:chatgpt` 等可能不存在的分类
- 即使 geosite.dat 是空的，配置也能正常运行

### 无视伪装域名
- Reality 节点无论 SNI 伪装成什么域名
- 都会自动落入 `MATCH,🔰 节点选择` 兜底规则

### 规则结构
```yaml
rules:
  # P2P 保护：避免 P2P 流量占用 VPS 带宽
  - PROCESS-NAME,Thunder.exe,DIRECT
  - PROCESS-NAME,qBittorrent.exe,DIRECT
  # ...

  # 局域网直连
  - GEOIP,lan,DIRECT,no-resolve

  # AI 专项 (硬绑定节点，保持连接稳定)
  - DOMAIN-SUFFIX,openai.com,{{节点名称}}
  - DOMAIN-SUFFIX,chatgpt.com,{{节点名称}}
  - DOMAIN-SUFFIX,claude.ai,{{节点名称}}
  # ... 更多 AI 域名

  # 国内直连
  - GEOSITE,cn,DIRECT
  - GEOIP,CN,DIRECT,no-resolve

  # 终极兜底
  - MATCH,🔰 节点选择
```

## 订阅地址

部署成功后：

```
http://<server_ip>:<random_port>/sub/<subId>
```

在 Clash Verge Rev 中：配置 → + → 远程 → 填入订阅地址 → 导入

## 示例输出

```
=======================================================
  ✅ 部署完成! — 部署报告
=======================================================

📋 服务器信息
  服务器 IP: 1.2.3.4
  主机名: vps-server
  操作系统: Debian 12

🔧 服务状态
  3x-ui:     ✅ active (端口: 2053)
  BBR:       ✅ bbr
  订阅服务:   ✅ active (端口: 38472)

📡 订阅信息
  订阅地址: http://1.2.3.4:38472/sub/<subId>

👤 已配置用户
  • user@example.com: abc123def456

🌐 管理面板
  3x-ui: http://1.2.3.4:2053
=======================================================
```

## 常见问题

### 3x-ui 安装需要交互

脚本会尝试自动应答，但部分情况可能需要手动 SSH 执行：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)
```

### 查看日志

```bash
ssh root@<server> "journalctl -u sub-server -f"
```

### 套 Nginx/Caddy 反代

订阅服务自动识别 `X-Real-IP` 和 `X-Forwarded-For` 头，速率限制正常生效。

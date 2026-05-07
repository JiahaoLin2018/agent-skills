# Action: deploy — 一键全流程部署

## 目标

一键完成 VPS 全流程部署：安装 3x-ui + 开启 BBR + 部署订阅服务。

## 执行步骤

### 执行部署脚本

```bash
python ~/.claude/skills/setup-transfer-clash/scripts/full_deploy.py
```

脚本会提示输入 SSH 连接信息：
- 服务器 IP（必填）
- SSH 端口（默认 22）
- 用户名（默认 root）
- 密码（必填）

### 执行流程

```
[1/4] 安装 3x-ui
  ├── 检测是否已安装
  ├── 下载官方安装脚本
  └── 自动应答完成安装

[2/4] 开启 BBR
  ├── 检查内核版本（需 4.9+）
  ├── 写入 /etc/sysctl.conf
  └── 验证生效

[3/4] 部署订阅服务
  ├── 自动获取公网 IP
  ├── 随机生成端口（10000-65535）
  ├── 上传 sub_server.py + config.conf
  ├── 创建 systemd 服务
  ├── 开放防火墙端口
  └── 启动并验证

[4/4] 输出部署报告
```

### 输出示例

```
=======================================================
  ✅ 部署完成! — 部署报告
=======================================================

📋 服务器信息
  服务器 IP: 1.2.3.4
  主机名: vps-server
  操作系统: Debian 12
  内核版本: 6.1.0-18-amd64

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

### 前置要求

- VPS 系统：Debian / Ubuntu（推荐）/ CentOS
- 本地已安装 paramiko：`pip install paramiko`

### 配置模板特点

部署后的配置模板具有以下特点：

| 特点 | 说明 |
|------|------|
| **零报错** | AI 规则用域名后缀，不依赖 geosite 数据库 |
| **Fake-IP** | 秒开网页，198.18.0.1/16 |
| **Sniffer** | 识别 TLS/HTTP/QUIC 流量 |
| **AI 隔离** | OpenAI/Claude/Gemini 强制走代理 |
| **自动测速** | 每 10 分钟测速显示延迟 |

### 部署后操作

1. 登录 3x-ui 面板创建 VLESS-Reality 入站和用户
2. 记录用户的 subId
3. 使用订阅地址导入 Clash Verge Rev
4. 在 Clash Verge Rev 设置中选择 Mihomo 内核

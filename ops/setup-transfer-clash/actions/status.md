# Action: status — 检查服务状态

## 目标

检查 VPS 上所有服务的运行状态。

## 执行步骤

### 使用 Python 脚本检查

```python
import os
import paramiko
import getpass

# 提示输入 SSH 信息
host = input('服务器 IP: ').strip()
port = input('SSH 端口 [22]: ').strip() or '22'
user = input('用户名 [root]: ').strip() or 'root'
password = getpass.getpass('密码: ')

# 连接服务器
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=host, port=int(port), username=user, password=password, timeout=10)

def run(cmd):
    _, stdout, _ = client.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='ignore').strip()

# 读取订阅端口
config = run('cat /opt/sub-server/config.conf 2>/dev/null')
sub_port = '3000'
for line in config.splitlines():
    if line.startswith('SUB_PORT='):
        sub_port = line.split('=')[1]
        break

print('=' * 55)
print('  📊 服务状态检查')
print('=' * 55)

# 系统信息
print('\n📋 系统信息')
print(f'  主机名: {run("hostname")}')
print(f'  运行时间: {run("uptime -p")}')
print(f'  内存: {run("free -h | grep Mem | awk \"{print \\$3\\\"/\\\"\\$2}\"")}')
print(f'  内核: {run("uname -r")}')

# 3x-ui
print('\n🔧 3x-ui')
xui = run('systemctl is-active x-ui 2>/dev/null || echo "inactive"')
icon = '✅' if xui == 'active' else '❌'
print(f'  服务状态: {icon} {xui}')

# BBR
print('\n🚀 BBR')
bbr = run('sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null')
icon = '✅' if 'bbr' in bbr.lower() else '⚠️'
print(f'  拥塞控制: {icon} {bbr}')

# 订阅服务
print('\n📡 订阅服务')
sub = run('systemctl is-active sub-server 2>/dev/null || echo "inactive"')
icon = '✅' if sub == 'active' else '❌'
print(f'  服务状态: {icon} {sub}')
print(f'  监听端口: {sub_port}')

ping = run(f'curl -s --max-time 5 http://127.0.0.1:{sub_port}/ping')
icon = '✅' if ping == 'pong' else '❌'
print(f'  健康检查: {icon} {ping}')

# 用户列表
print('\n👤 已配置用户 (subId)')
server_ip = run('curl -s --max-time 5 ifconfig.me 2>/dev/null')
users = run('''python3 -c "
import sqlite3, json
try:
    conn = sqlite3.connect('/etc/x-ui/x-ui.db')
    c = conn.cursor()
    c.execute('SELECT settings FROM inbounds WHERE enable=1')
    for row in c.fetchall():
        for client in json.loads(row[0] or '{}').get('clients', []):
            sub_id = client.get('subId', '')
            email = client.get('email', 'N/A')
            if sub_id:
                print(f'  • {email}: {sub_id}')
    conn.close()
except: pass
" 2>/dev/null''')
print(users if users.strip() else '  暂无用户')

# 日志
print('\n📜 最近日志')
logs = run('journalctl -u sub-server -n 5 --no-pager 2>/dev/null')
for line in logs.splitlines():
    print(f'  {line}')

client.close()

print('\n' + '=' * 55)
print(f'📡 订阅地址: http://{server_ip}:{sub_port}/sub/<subId>')
print('=' * 55)
```

### 输出示例

```
=======================================================
  📊 服务状态检查
=======================================================

📋 系统信息
  主机名: vps-server
  运行时间: up 2 days
  内存: 317Mi/967Mi
  内核: 6.1.0-18-amd64

🔧 3x-ui
  服务状态: ✅ active

🚀 BBR
  拥塞控制: ✅ bbr

📡 订阅服务
  服务状态: ✅ active
  监听端口: 38472
  健康检查: ✅ pong

👤 已配置用户 (subId)
  • user@example.com: abc123def456

📜 最近日志
  Mar 27 10:00:01 server sub_server.py[1234]: 生成订阅: 用户=user@example.com

=======================================================
📡 订阅地址: http://1.2.3.4:38472/sub/<subId>
=======================================================
```

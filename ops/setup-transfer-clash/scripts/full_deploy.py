#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS 一键部署脚本
自动完成：安装 3x-ui + 开启 BBR + 部署订阅服务

用法: python full_deploy.py
执行时会提示输入 SSH 连接信息
"""

import paramiko
import os
import sys
import time
import random
import getpass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REMOTE_DIR = '/opt/sub-server'
SERVICE_FILE = '/etc/systemd/system/sub-server.service'


def prompt_ssh_info():
    """提示用户输入 SSH 连接信息"""
    print('\n请输入 VPS SSH 连接信息:')
    print('(直接回车使用默认值)\n')

    host = input('  服务器 IP [必填]: ').strip()
    if not host:
        print('  ❌ 服务器 IP 不能为空')
        sys.exit(1)

    port = input('  SSH 端口 [22]: ').strip() or '22'
    user = input('  用户名 [root]: ').strip() or 'root'
    password = getpass.getpass('  密码 [必填]: ').strip()
    if not password:
        print('  ❌ 密码不能为空')
        sys.exit(1)

    return {
        'VPS_HOST': host,
        'VPS_SSH_PORT': port,
        'VPS_USER': user,
        'VPS_PASSWORD': password,
    }


def random_port():
    """生成随机端口（10000-65535）"""
    return str(random.randint(10000, 65535))


def run(client, cmd, desc=None, timeout=120, check=False, silent=False):
    """执行远程命令"""
    if desc and not silent:
        print(f'  [{desc}]')
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()

    if out and not silent:
        for line in out.splitlines()[:20]:
            print(f'    {line}')
    if check and err and 'warning' not in err.lower() and not silent:
        for line in err.splitlines()[:10]:
            print(f'    [err] {line}')
    return out


def make_systemd_service():
    """生成 systemd 服务文件"""
    return b"""\
[Unit]
Description=Clash Subscription Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/sub-server
ExecStart=/usr/bin/python3 /opt/sub-server/sub_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""


def make_server_config(server_ip, sub_port, db_path='/etc/x-ui/x-ui.db'):
    """生成服务器端配置文件"""
    return (
        f"SERVER_IP={server_ip}\n"
        f"SUB_PORT={sub_port}\n"
        f"DB_PATH={db_path}\n"
        f"LOG_FILE=/opt/sub-server/sub.log\n"
        f"REQUEST_TIMEOUT=10\n"
    ).encode('utf-8')


def detect_os(client):
    """检测操作系统类型"""
    out = run(client, 'cat /etc/os-release 2>/dev/null | head -5', timeout=10, silent=True)
    if 'debian' in out.lower() or 'ubuntu' in out.lower():
        return 'debian'
    elif 'centos' in out.lower() or 'rhel' in out.lower():
        return 'centos'
    return 'debian'


def install_3xui(client):
    """安装 3x-ui，返回 (success, panel_port)"""
    print('\n' + '=' * 55)
    print('  [1/4] 安装 3x-ui')
    print('=' * 55)

    # 检查是否已安装
    status = run(client, 'systemctl is-active x-ui 2>/dev/null || echo "NOT_INSTALLED"', silent=True)
    if status.strip() == 'active':
        print('  3x-ui 已安装且运行中，跳过安装')
        return True, '2053'

    # 检查 x-ui 命令
    has_xui = run(client, 'which x-ui 2>/dev/null || echo "NO"', silent=True)
    if 'x-ui' in has_xui:
        print('  3x-ui 已安装，尝试启动...')
        run(client, 'systemctl start x-ui', timeout=30)
        time.sleep(3)
        status = run(client, 'systemctl is-active x-ui 2>/dev/null || echo "inactive"', silent=True)
        if status.strip() == 'active':
            print('  3x-ui 启动成功')
            return True, '2053'

    print('  正在安装 3x-ui，请耐心等待（约 2-5 分钟）...')

    # 使用官方安装脚本
    install_cmd = 'bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)'
    result = run(client, f'yes "" | {install_cmd}', desc='下载并安装 3x-ui', timeout=600, check=True)

    time.sleep(5)

    # 验证安装
    status = run(client, 'systemctl is-active x-ui 2>/dev/null || echo "inactive"', silent=True)
    if status.strip() == 'active':
        print('  ✅ 3x-ui 安装成功')
        return True, '2053'
    else:
        print('  ⚠️ 3x-ui 安装可能需要交互，请手动执行：')
        print('     bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/master/install.sh)')
        return False, '2053'


def enable_bbr(client):
    """开启 BBR"""
    print('\n' + '=' * 55)
    print('  [2/4] 开启 BBR')
    print('=' * 55)

    kernel = run(client, 'uname -r', silent=True)
    print(f'  内核版本: {kernel}')

    # 检查当前状态
    current = run(client, 'sysctl net.ipv4.tcp_congestion_control 2>/dev/null', silent=True)
    if 'bbr' in current.lower():
        print('  BBR 已开启，跳过配置')
        return True

    # 配置 BBR
    run(client, 'echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf', silent=True)
    run(client, 'echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf', silent=True)
    run(client, 'sysctl -p', desc='应用 BBR 配置')

    # 验证
    verify = run(client, 'sysctl net.ipv4.tcp_congestion_control 2>/dev/null', silent=True)
    if 'bbr' in verify.lower():
        print('  ✅ BBR 开启成功')
        return True
    else:
        print(f'  ⚠️ BBR 开启失败，当前: {verify}')
        return False


def deploy_sub_service(client, sftp):
    """部署订阅服务，返回 (server_ip, sub_port) 或 (None, None)"""
    print('\n' + '=' * 55)
    print('  [3/4] 部署订阅服务')
    print('=' * 55)

    # 获取服务器公网 IP
    print('  获取服务器公网 IP...')
    server_ip = run(client, 'curl -s --max-time 10 ifconfig.me 2>/dev/null || curl -s --max-time 10 ip.sb 2>/dev/null', silent=True)
    server_ip = server_ip.strip() if server_ip.strip() else None

    if not server_ip:
        print('  ❌ 无法获取公网 IP')
        return None, None

    print(f'  公网 IP: {server_ip}')

    # 生成随机端口
    sub_port = random_port()
    print(f'  订阅端口: {sub_port} (随机生成)')

    # 检测 x-ui 数据库路径
    db_path = '/etc/x-ui/x-ui.db'
    db_check = run(client, f'ls {db_path} 2>/dev/null || echo "NOT_FOUND"', silent=True)
    if 'NOT_FOUND' in db_check:
        alt_db = run(client, 'find /etc/x-ui /usr/local/x-ui -name "x-ui.db" 2>/dev/null | head -1', silent=True)
        if alt_db.strip():
            db_path = alt_db.strip()
            print(f'  数据库路径: {db_path}')

    # 创建目录
    run(client, f'mkdir -p {REMOTE_DIR}', silent=True)

    # 上传脚本
    print('  上传订阅服务脚本...')
    local_script = os.path.join(SCRIPT_DIR, 'sub_server.py')
    if os.path.exists(local_script):
        with open(local_script, 'rb') as f:
            script_content = f.read()
        with sftp.open(f'{REMOTE_DIR}/sub_server.py', 'wb') as f:
            f.write(script_content)
    else:
        print(f'  ❌ 脚本文件不存在: {local_script}')
        return None, None

    # 上传配置
    with sftp.open(f'{REMOTE_DIR}/config.conf', 'wb') as f:
        f.write(make_server_config(server_ip, sub_port, db_path))

    # 安装 systemd 服务
    print('  创建 systemd 服务...')
    with sftp.open(SERVICE_FILE, 'wb') as f:
        f.write(make_systemd_service())
    run(client, 'systemctl daemon-reload', silent=True)
    run(client, 'systemctl enable sub-server', silent=True)

    # 开放防火墙端口
    print(f'  开放端口 {sub_port}...')
    has_ufw = run(client, 'which ufw 2>/dev/null', silent=True)
    if has_ufw.strip():
        run(client, f'ufw allow {sub_port}/tcp comment "Clash Sub" 2>/dev/null', silent=True)
    else:
        run(client, f'iptables -C INPUT -p tcp --dport {sub_port} -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport {sub_port} -j ACCEPT', silent=True)

    # 启动服务
    print('  启动服务...')
    run(client, 'systemctl restart sub-server', silent=True)
    time.sleep(3)

    # 验证
    status = run(client, 'systemctl is-active sub-server 2>/dev/null', silent=True)
    if status.strip() == 'active':
        ping = run(client, f'curl -s --max-time 5 http://127.0.0.1:{sub_port}/ping', silent=True)
        if ping == 'pong':
            print('  ✅ 订阅服务部署成功')
            return server_ip, sub_port
        else:
            print(f'  ⚠️ 服务运行但健康检查失败: {ping}')
    else:
        print(f'  ❌ 服务启动失败')
        run(client, 'journalctl -u sub-server -n 20 --no-pager', desc='查看错误日志')

    return server_ip, sub_port


def get_users(client, db_path):
    """获取用户列表"""
    users = run(client, f'''python3 -c "
import sqlite3, json
try:
    conn = sqlite3.connect('{db_path}')
    c = conn.cursor()
    c.execute('SELECT settings FROM inbounds WHERE enable=1')
    users = []
    for row in c.fetchall():
        for client in json.loads(row[0] or '{{}}').get('clients', []):
            sub_id = client.get('subId', '')
            email = client.get('email', 'N/A')
            if sub_id:
                users.append(f'{email}|{sub_id}')
    print('\\n'.join(users))
    conn.close()
except:
    pass
" 2>/dev/null''', silent=True)
    result = []
    for line in users.strip().splitlines():
        if '|' in line:
            email, sub_id = line.split('|', 1)
            result.append((email, sub_id))
    return result


def print_deploy_report(client, server_ip, sub_port, db_path, xui_ok, bbr_ok, panel_port):
    """打印部署报告"""
    # 获取系统信息
    hostname = run(client, 'hostname', silent=True)
    os_info = run(client, 'cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d \\"', silent=True)
    kernel = run(client, 'uname -r', silent=True)

    # 服务状态
    xui_status = run(client, 'systemctl is-active x-ui 2>/dev/null || echo "inactive"', silent=True)
    sub_status = run(client, 'systemctl is-active sub-server 2>/dev/null || echo "inactive"', silent=True)
    bbr_status = run(client, 'sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null', silent=True)

    # 用户列表
    users = get_users(client, db_path)

    print('\n' + '=' * 55)
    print('  ✅ 部署完成! — 部署报告')
    print('=' * 55)

    print('\n📋 服务器信息')
    print(f'  服务器 IP: {server_ip}')
    print(f'  主机名: {hostname}')
    print(f'  操作系统: {os_info or "Unknown"}')
    print(f'  内核版本: {kernel}')

    print('\n🔧 服务状态')
    xui_icon = '✅' if xui_status == 'active' else '❌'
    bbr_icon = '✅' if 'bbr' in bbr_status.lower() else '⚠️'
    sub_icon = '✅' if sub_status == 'active' else '❌'
    print(f'  3x-ui:     {xui_icon} {xui_status} (端口: {panel_port})')
    print(f'  BBR:       {bbr_icon} {bbr_status}')
    print(f'  订阅服务:   {sub_icon} {sub_status} (端口: {sub_port})')

    print('\n📡 订阅信息')
    print(f'  订阅地址: http://{server_ip}:{sub_port}/sub/<subId>')

    print('\n👤 已配置用户')
    if users:
        for email, sub_id in users:
            print(f'  • {email}: {sub_id}')
    else:
        print('  暂无用户（请在 3x-ui 面板添加）')

    print('\n🌐 管理面板')
    print(f'  3x-ui: http://{server_ip}:{panel_port}')

    print('\n' + '=' * 55)


def main():
    print('=' * 55)
    print('  🚀 VPS 一键部署工具')
    print('  3x-ui + BBR + Clash 订阅服务')
    print('=' * 55)

    # 获取 SSH 信息
    ssh_info = prompt_ssh_info()

    # 连接服务器
    print('\n[连接] SSH 连接服务器...')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=ssh_info['VPS_HOST'],
            port=int(ssh_info['VPS_SSH_PORT']),
            username=ssh_info['VPS_USER'],
            password=ssh_info['VPS_PASSWORD'],
            timeout=15,
        )
    except Exception as e:
        print(f'  ❌ 连接失败: {e}')
        sys.exit(1)

    print('  ✅ 连接成功')

    # 检测操作系统
    os_type = detect_os(client)
    print(f'  系统类型: {os_type}')

    sftp = client.open_sftp()

    try:
        # 1. 安装 3x-ui
        xui_ok, panel_port = install_3xui(client)

        # 2. 开启 BBR
        bbr_ok = enable_bbr(client)

        # 3. 部署订阅服务
        server_ip, sub_port = deploy_sub_service(client, sftp)

        if server_ip and sub_port:
            # 检测数据库路径
            db_path = '/etc/x-ui/x-ui.db'
            db_check = run(client, f'ls {db_path} 2>/dev/null || echo "NOT_FOUND"', silent=True)
            if 'NOT_FOUND' in db_check:
                alt_db = run(client, 'find /etc/x-ui /usr/local/x-ui -name "x-ui.db" 2>/dev/null | head -1', silent=True)
                if alt_db.strip():
                    db_path = alt_db.strip()

            # 4. 打印部署报告
            print_deploy_report(client, server_ip, sub_port, db_path, xui_ok, bbr_ok, panel_port)
        else:
            print('\n  ❌ 订阅服务部署失败')

    except Exception as e:
        print(f'\n  ❌ 部署出错: {e}')
        import traceback
        traceback.print_exc()
    finally:
        sftp.close()
        client.close()


if __name__ == '__main__':
    main()

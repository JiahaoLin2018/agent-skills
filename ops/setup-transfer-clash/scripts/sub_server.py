#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash 订阅服务 - 部署在 VPS 上
实时读取 3x-ui SQLite 数据库，生成 Clash Meta 原生 YAML
无需 Sub-Store / SubConverter，零额外依赖

订阅链接格式: http://<server_ip>:<port>/sub/<3x-ui的subId>
"""

# ═══════════════════════════════════════════════════════════════════
# 📋 CLASH META (MIHOMO) 配置模板
# ═══════════════════════════════════════════════════════════════════

CLASH_CONFIG_TEMPLATE = '''# =================================================================
# 🛡️ CLASH VERGE REV 极简终极毕业版配置文件 (自建单节点专属)
# 适用内核: Mihomo (原 Meta) 内核
# 设计理念: 极致清爽 UI / 真实 IP 零维护 (KISS原则) / AI 硬绑定保持稳定 / VPS 带宽保护
# =================================================================

# ==========================================
# 1️⃣ 基础全局设置 (Global Settings)
# ==========================================
# [混合端口] 监听本地 7890 端口，同时支持 HTTP 和 SOCKS5 代理协议
mixed-port: 7890
# [IPv6 开关] 强烈建议 false。国内 IPv6 支持度参差不齐，开启易导致分流乱窜或节点连不上
ipv6: false
# [运行模式] rule 表示按下方设置的规则分流；global 是全代理；direct 是全直连
mode: rule
# [日志级别] info 是最平衡的级别，平时不占用性能，出问题时能看到连接日志
log-level: info
# [统一延迟] true 会在测速时把 TCP 和 TLS 握手时间算进去，测出来的延迟更贴近真实体验
unified-delay: true

# ==========================================
# 2️⃣ 流量嗅探 (Sniffer) - 🌟 核心保留
# ==========================================
# [作用] 很多 App (如手机版 ChatGPT) 为了防劫持，会绕过系统 DNS 直接用 IP 发请求。
# 开启嗅探后，内核能从数据包中"闻"出真实的域名，从而让下方的分流规则生效。极大地提升代理精确度。
sniffer:
  enable: true
  sniff:
    TLS:
      ports: [443, 8443]     # 拦截并嗅探 HTTPS 加密流量中的 SNI 域名
    HTTP:
      ports: [80, 8080-8880] # 拦截普通 HTTP 流量提取 Host
    QUIC:
      ports: [443]           # Google 和 Meta 系应用常用的 UDP QUIC 协议
  # [防死循环] 防止嗅探器截获国内特殊 P2P 软件或局域网服务，确保本地网络纯净
  skip-domain:
    - '+.lan'
    - '+.local'
    - '+.oray.com'
    - '+.oray.net'
    - '+.sunlogin.net'

# ==========================================
# 3️⃣ DNS 增强模块 (DNS Module) - 🌟 回归 KISS 原则
# ==========================================
# [优化说明] 彻底移除臃肿的 Fake-IP 模式及上百行的黑名单。
# 恢复使用基础真实 IP 解析，彻底解决局域网断网、向日葵连不上等痛点，实现真正的 0 维护。
dns:
  enable: true
  ipv6: false
  # [系统 Hosts] 继承电脑系统的 hosts 规则，保护本地开发和去广告映射
  use-hosts: true

  # [引导 DNS] 仅用于解析下方 DoH 服务器本身的域名
  default-nameserver:
    - 223.5.5.5
    - 119.29.29.29

  # [智能策略] 核心精髓：国内域名直接走国内 DNS，速度最快，不走代理
  nameserver-policy:
    "geosite:cn,private": [https://doh.pub/dns-query, https://dns.alidns.com/dns-query]

  # [默认 DNS] 除国内域名外，所有流量默认走海外纯净 DNS（DoH 协议）
  # 这样配置后，无需额外写 fallback-filter，因为所有走这里的请求都是为了获取纯净 IP
  nameserver:
    - https://dns.google/dns-query
    - https://1.1.1.1/dns-query

# ==========================================
# 4️⃣ 节点配置 (Proxies)
# ==========================================
proxies:
{{PROXIES}}


# ==========================================
# 5️⃣ 代理组 (Proxy Groups) - 极简模式
# ==========================================
proxy-groups:
  - name: 🔰 节点选择
    type: select
    proxies:
      - VLESS-Reality
      - DIRECT          # 走直连。当你需要大文件下载，不想跑 VPS 流量时，可手动切成这个

# ==========================================
# 6️⃣ 规则分流 (Rules)
# ==========================================
rules:
  # 0. 🛡️ 强制 P2P 下载流量直连，避免占用 VPS 带宽影响主线路 (核心防御，不可删)
  - PROCESS-NAME,Thunder.exe,DIRECT
  - PROCESS-NAME,Thunder,DIRECT
  - PROCESS-NAME,qBittorrent.exe,DIRECT
  - PROCESS-NAME,qBittorrent,DIRECT
  - PROCESS-NAME,BitComet.exe,DIRECT
  - PROCESS-NAME,BitComet,DIRECT
  - PROCESS-NAME,Transmission.exe,DIRECT
  - PROCESS-NAME,Transmission,DIRECT
  - PROCESS-NAME,aria2c.exe,DIRECT
  - PROCESS-NAME,aria2c,DIRECT
  - PROCESS-NAME,fdm.exe,DIRECT
  - PROCESS-NAME,fdm,DIRECT
  - PROCESS-NAME,uTorrent.exe,DIRECT
  - PROCESS-NAME,uTorrent,DIRECT
  - PROCESS-NAME,WebTorrent.exe,DIRECT
  - PROCESS-NAME,WebTorrent,DIRECT

  # 1. ⚔️ 协议降级：拒绝 UDP 443 (QUIC)，强迫各种 App 和 CLI 工具走极度稳定的 TCP (大幅缓解跨国断流)
  - AND,((NETWORK,UDP),(DST-PORT,443)),REJECT

  # 2. 🏠 局域网直连 (防止内网设备互访走代理)
  - GEOIP,lan,DIRECT,no-resolve

  # 3. 🤖 AI 与 Google 专项硬绑定 (防手滑切 DIRECT 导致 IP 跳动连接中断)
  - DOMAIN-SUFFIX,openai.com,VLESS-Reality
  - DOMAIN-SUFFIX,chatgpt.com,VLESS-Reality
  - DOMAIN-SUFFIX,oaistatic.com,VLESS-Reality
  - DOMAIN-SUFFIX,oaiusercontent.com,VLESS-Reality
  - DOMAIN-SUFFIX,anthropic.com,VLESS-Reality
  - DOMAIN-SUFFIX,claude.ai,VLESS-Reality
  - DOMAIN-SUFFIX,datadoghq.com,VLESS-Reality
  - DOMAIN-SUFFIX,googleapis.com,VLESS-Reality
  - DOMAIN-SUFFIX,google.com,VLESS-Reality
  - DOMAIN-SUFFIX,gstatic.com,VLESS-Reality
  - DOMAIN-SUFFIX,googleusercontent.com,VLESS-Reality
  - DOMAIN-SUFFIX,gemini.google.com,VLESS-Reality
  - DOMAIN-SUFFIX,aistudio.google.com,VLESS-Reality
  - DOMAIN-SUFFIX,ai.google.dev,VLESS-Reality
  - DOMAIN-SUFFIX,perplexity.ai,VLESS-Reality
  - DOMAIN-SUFFIX,poe.com,VLESS-Reality

  # 4. 🇨🇳 国内直连兜底 (靠 IP 自动判定，完美接住向日葵等国内服务，配合 sniffer 豁免)
  - GEOIP,CN,DIRECT,no-resolve

  # 5. 🌐 终极兜底
  - MATCH,🔰 节点选择
'''

# ═══════════════════════════════════════════════════════════════════
# 节点配置模板 (单个节点) - 保留行内注释
# ═══════════════════════════════════════════════════════════════════

PROXY_TEMPLATE = '''  - name: "VLESS-Reality"
    type: vless
    server: {server}
    port: {port}
    uuid: {uuid}
    cipher: auto
    tls: true
    udp: true                    # 开启 UDP 支持 (重要：用于语音通话/视频流/打游戏)
    flow: {flow}                 # Vision 流控：减少 TLS 握手开销，防主动探测，目前 VLESS 最优解
    servername: {servername}     # SNI 伪装域名：必须与你在服务端配置的 dest/serverNames 完全一致！
    network: {network}
    reality-opts:
      public-key: {public_key}
      short-id: {short_id}
    client-fingerprint: {fingerprint}  # 模拟 Chrome 浏览器指纹，防止 GFW 识别特征'''

# ═══════════════════════════════════════════════════════════════════
# 程序主体
# ═══════════════════════════════════════════════════════════════════

import sqlite3
import json
import logging
import os
import socket
import random
from collections import defaultdict, deque
from time import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.conf')


def random_port():
    """生成5位随机端口（10000-65535）"""
    return str(random.randint(10000, 65535))


def load_config(path):
    """读取 KEY=VALUE 格式的配置文件"""
    config = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    config[key.strip()] = value.strip()
    return config


def init_config():
    """初始化配置文件：不存在则创建，存在则读取"""
    defaults = {
        'SUB_PORT': random_port(),
        'DB_PATH': '/etc/x-ui/x-ui.db',
        'SERVER_IP': '',
        'LOG_FILE': '/opt/sub-server/sub.log',
        'REQUEST_TIMEOUT': '10',
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            for key, value in defaults.items():
                f.write(f'{key}={value}\n')
        return defaults
    return load_config(CONFIG_FILE)

# 加载配置
_raw = init_config()

# 环境变量可覆盖配置文件
for key in ['SERVER_IP', 'SUB_PORT', 'DB_PATH', 'LOG_FILE', 'REQUEST_TIMEOUT']:
    if key in os.environ:
        _raw[key] = os.environ[key]

CONFIG = {
    'port':             int(_raw.get('SUB_PORT', random_port())),
    'db_path':          _raw.get('DB_PATH', '/etc/x-ui/x-ui.db'),
    'server_ip':        _raw.get('SERVER_IP', ''),
    'log_file':         _raw.get('LOG_FILE', '/opt/sub-server/sub.log'),
    'request_timeout':  int(_raw.get('REQUEST_TIMEOUT', 10)),
    'rate_limit':       int(_raw.get('RATE_LIMIT', 10)),
    'rate_window':      int(_raw.get('RATE_WINDOW', 60)),
}

# 速率限制：每个 IP 独立计数
request_history = defaultdict(deque)

# 创建日志目录
log_dir = os.path.dirname(CONFIG['log_file'])
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file']),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


def check_rate_limit(ip):
    """滑动窗口速率限制：每个 IP 在 window 秒内最多 limit 次请求"""
    limit = CONFIG.get('rate_limit', 10)
    window = CONFIG.get('rate_window', 60)
    now = time()
    history = request_history[ip]

    # 移除窗口外的过期记录
    while history and now - history[0] > window:
        history.popleft()

    if len(history) >= limit:
        return False

    history.append(now)
    return True


def validate_sub_id(sub_id):
    """校验 subId 格式，防止路径遍历"""
    if not sub_id or len(sub_id) > 64:
        return False
    # 防止路径遍历攻击
    if '..' in sub_id or '/' in sub_id or '\\' in sub_id:
        return False
    return True


# ────────────────────────────────────────────────
# 数据读取层
# ────────────────────────────────────────────────

def get_subscription_data(sub_id):
    """根据 subId 一次性查询用户信息和入站配置"""
    conn = sqlite3.connect(CONFIG['db_path'])
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                json_extract(c.value, '$.id') AS uuid,
                json_extract(c.value, '$.email') AS email,
                json_extract(c.value, '$.flow') AS flow,
                i.port,
                i.stream_settings
            FROM inbounds i,
                 json_each(json_extract(i.settings, '$.clients')) c
            WHERE i.protocol = 'vless'
              AND i.enable = 1
              AND json_extract(i.stream_settings, '$.security') = 'reality'
              AND json_extract(c.value, '$.subId') = ?
            LIMIT 1
        """, (sub_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return {
                'uuid': row[0],
                'email': row[1] or '',
                'flow': row[2] or 'xtls-rprx-vision',
                'port': row[3],
                'stream_settings': row[4],
            }
        return None
    finally:
        conn.close()


# ────────────────────────────────────────────────
# 协议解析层
# ────────────────────────────────────────────────

def parse_proxy_config(data):
    """解析节点配置"""
    try:
        stream = json.loads(data['stream_settings'] or '{}')
    except json.JSONDecodeError as e:
        log.warning(f"JSON 解析失败: {e}")
        return None

    reality = stream.get('realitySettings', {})
    reality_inner = reality.get('settings', {})
    public_key = reality_inner.get('publicKey', '')
    if not public_key:
        return None

    return {
        'server': CONFIG['server_ip'],
        'port': int(data['port']),
        'uuid': data['uuid'],
        'network': stream.get('network', 'tcp'),
        'flow': data['flow'],
        'servername': (reality.get('serverNames') or [''])[0],
        'fingerprint': reality_inner.get('fingerprint', 'chrome'),
        'public_key': public_key,
        'short_id': (reality.get('shortIds') or [''])[0],
    }


# ────────────────────────────────────────────────
# YAML 生成层
# ────────────────────────────────────────────────

def format_proxy_yaml(proxy):
    """将节点配置格式化为 YAML"""
    return PROXY_TEMPLATE.format(
        server=proxy['server'],
        port=proxy['port'],
        uuid=proxy['uuid'],
        flow=proxy['flow'],
        servername=proxy['servername'],
        network=proxy['network'],
        public_key=proxy['public_key'],
        short_id=proxy['short_id'],
        fingerprint=proxy['fingerprint'],
    )


def build_clash_yaml(proxy):
    """生成 Clash Meta YAML 配置"""
    proxies_yaml = format_proxy_yaml(proxy)
    return CLASH_CONFIG_TEMPLATE.replace('{{PROXIES}}', proxies_yaml)


def get_profile_name(user_email=None):
    """生成 profile 名称：前缀 Buddy + 后缀邮箱"""
    if user_email:
        return f"Buddy ({user_email})"
    return "Buddy"


# ────────────────────────────────────────────────
# 业务逻辑层
# ────────────────────────────────────────────────

def generate_subscription(sub_id):
    """生成订阅配置"""
    data = get_subscription_data(sub_id)
    if not data:
        return None, 'sub_id_not_found', None

    proxy = parse_proxy_config(data)
    if not proxy:
        return None, 'no_nodes', None

    user_email = data['email']
    log.info(f"生成订阅: 邮箱={user_email} UUID={data['uuid'][:8]}...")
    return build_clash_yaml(proxy), None, user_email


# ────────────────────────────────────────────────
# HTTP 服务层
# ────────────────────────────────────────────────

class SubHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    protocol_version = 'HTTP/1.1'
    timeout = CONFIG.get('request_timeout', 10)

    def setup(self):
        BaseHTTPRequestHandler.setup(self)
        try:
            self.connection.settimeout(self.timeout)
        except Exception:
            self.close_connection = True

    def handle_one_request(self):
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except (ConnectionResetError, BrokenPipeError, socket.timeout):
            self.close_connection = True

    def do_GET(self):
        try:
            parts = [p for p in urlparse(self.path).path.strip('/').split('/') if p]

            if len(parts) == 2 and parts[0] == 'sub':
                self._handle_sub(parts[1])
            elif len(parts) == 1 and parts[0] == 'ping':
                self._respond(200, b'pong')
            else:
                self._respond(404, b'Not found')

        except (ConnectionResetError, BrokenPipeError, socket.timeout) as e:
            log.debug(f"连接异常 from {self.client_address[0]}: {type(e).__name__}")

    def _handle_sub(self, sub_id):
        # 优先级：X-Real-IP > X-Forwarded-For (取第一个) > client_address
        client_ip = (
            self.headers.get('X-Real-IP') or
            self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
            self.client_address[0]
        )

        # 速率限制检查
        if not check_rate_limit(client_ip):
            log.warning(f"速率限制触发 from {client_ip}")
            self._respond(429, b'Too many requests')
            return

        # subId 格式校验
        if not validate_sub_id(sub_id):
            log.warning(f"无效 subId [{sub_id}] from {client_ip}")
            self._respond(400, b'Invalid subscription ID')
            return

        try:
            content, err, user_email = generate_subscription(sub_id)
        except Exception as e:
            log.error(f"生成订阅异常: {e}", exc_info=True)
            self._respond(500, b'Internal server error')
            return

        if err == 'sub_id_not_found':
            log.warning(f"未找到 subId [{sub_id}] from {client_ip}")
            self._respond(404, b'Subscription ID not found')
            return
        if err == 'no_nodes':
            log.warning(f"subId [{sub_id}] 无可用节点")
            self._respond(404, b'No nodes found')
            return

        self._send_yaml(content, user_email)

    def _send_yaml(self, content, user_email=None):
        """发送 YAML 响应"""
        profile = get_profile_name(user_email)
        body = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/yaml; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename={profile}')
        self.send_header('profile-title', profile)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache, no-store')
        self.end_headers()
        self.wfile.write(body)

    def _respond(self, code, body):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    if not CONFIG['server_ip']:
        log.error('SERVER_IP 未配置')
        exit(1)

    port = CONFIG['port']
    log.info('=' * 55)
    log.info('Clash 订阅服务启动')
    log.info(f'监听端口: {port}')
    log.info(f'订阅地址: http://{CONFIG["server_ip"]}:{port}/sub/<subId>')
    log.info('=' * 55)

    server = ThreadingHTTPServer(('0.0.0.0', port), SubHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('服务停止')

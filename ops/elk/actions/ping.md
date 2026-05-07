# Action: ping

检查 Elasticsearch 集群连通性和健康状态。

## 命令格式

```
/elk ping
/elk ping uat
```

## 步骤

1. **加载配置（含自动检测）**：

   按 SKILL.md"配置加载流程"执行：检查配置文件是否存在，不存在则从模板自动创建。

   ```bash
   test -f ~/.claude/skill_config_elk.yml || cp <skill_dir>/templates/skill_config_elk-template.yml ~/.claude/skill_config_elk.yml
   ```

   若自动创建，告知用户"已从模板创建配置文件，使用默认连接信息进行 ping"。

2. **执行连通性检查**：
   ```bash
   # 生产环境（默认）
   python <skill_dir>/scripts/elk_api.py --connection prod ping

   # 测试环境（用户输入含 uat 关键词时）
   python <skill_dir>/scripts/elk_api.py --connection uat ping
   ```

3. **输出结果**：展示集群名称、节点数、分片状态（green/yellow/red）。

4. **连接失败处理**：若出现 `getaddrinfo failed` 或 DNS 解析错误，按以下步骤排查：

   **4.1 从配置文件提取域名**：
   ```bash
   cat ~/.claude/skill_config_elk.yml
   ```
   从 `connections.<env>.uri` 中提取主机名，例如：
   - `http://YOUR_PROD_ES_HOST:9200` → 主机名 `YOUR_PROD_ES_HOST`

   **4.2 询问用户该域名对应的 IP**：

   公司内网 ES 域名通常需要 hosts 解析或 VPN。让用户提供该域名对应的 IP（找运维/DevOps 同事获取，或在 Kibana 集群信息里查看），写入 hosts 即可。

   **4.3 检查是否已有 hosts 记录**：
   ```bash
   grep "<域名>" /c/Windows/System32/drivers/etc/hosts 2>/dev/null || \
   grep "<域名>" /etc/hosts 2>/dev/null
   ```

   **4.4 若无记录，提示用户写入**：

   执行写入（Windows）：
   ```bash
   # Git Bash 下（需管理员权限）
   echo '<用户提供的IP>  <域名>' >> /c/Windows/System32/drivers/etc/hosts
   ```

   若权限不足，提示以管理员身份运行：
   ```powershell
   powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList \"-Command Add-Content -Path 'C:\\Windows\\System32\\drivers\\etc\\hosts' -Value \\\"`n<IP>`t<域名>\\\"\""
   ```

   **4.5 写入后立即重新 ping 验证**：
   ```bash
   python <skill_dir>/scripts/elk_api.py --connection <env> ping
   ```
   若仍失败，告知用户需要连接公司内网或 VPN 后再试。

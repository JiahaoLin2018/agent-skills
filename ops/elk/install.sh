#!/usr/bin/env bash
# 通用 Skill 安装脚本
# 将当前目录的所有内容部署到 ~/.claude/skills/<skill_name>/
# skill 名称从目录名自动推导，无需手动修改

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="$(basename "$SRC")"
DST="${HOME}/.claude/skills/${SKILL_NAME}"

mkdir -p "$DST"
cp -r "$SRC"/. "$DST"/

echo "✅ ${SKILL_NAME} installed to ${DST}"
echo ""
echo "下一步："
echo "  1. 编辑配置文件：\$EDITOR ~/.claude/skill_config_${SKILL_NAME}.yml"
echo "     （详见 README.md 安装后配置章节）"
echo "  2. 在 Claude Code 中使用：/${SKILL_NAME} help"

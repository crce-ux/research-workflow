#!/usr/bin/env bash
# 拉取 ppt-master（PPTX 合并层）到本仓库的 vendor/。
#
# 为什么不在仓库里：ppt-master 是 **Hugo He** 的第三方 MIT 项目
#   https://github.com/hugohe3/ppt-master
# 它有 731 MB（其中 examples/ 占 581 MB）、依赖闭包跨 ~90 个文件、且在活跃维护。
# 整份塞进本仓库 = 背一个 fork 的债。所以改成：仓库里只放这个脚本，
# 需要时把它拉到 `vendor/`（已在 .gitignore 里）。
#
# 用法：  bash scripts/ppt/setup.sh
# 之后    ppt_build.py 会自动在 vendor/ 下找到它（见 _find_ppt_master）。
#
# 不想用 vendor/ 也可以：装到别处，再设环境变量 PPT_MASTER=<...>/svg_to_pptx.py

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 向上找到带 .git 的仓库根
ROOT="$HERE"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/.git" ]; do ROOT="$(dirname "$ROOT")"; done

DEST="$ROOT/vendor/ppt-master"
REPO="https://github.com/hugohe3/ppt-master.git"

if [ -d "$DEST/.git" ]; then
  echo "已存在，更新中：$DEST"
  git -C "$DEST" pull --ff-only
else
  echo "下载 ppt-master → $DEST"
  mkdir -p "$(dirname "$DEST")"
  git clone --depth 1 "$REPO" "$DEST"
fi

echo
echo "装 Python 依赖……"
python -m pip install -r "$DEST/skills/ppt-master/requirements.txt" \
  || echo "⚠️ pip 失败，手动跑：python -m pip install -r $DEST/skills/ppt-master/requirements.txt"

echo
echo "✅ 完成。ppt_build.py 会自动在 vendor/ 下找到合并层。"
echo "   （版权归 Hugo He，MIT；本仓库不分发它。）"

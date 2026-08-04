#!/usr/bin/env python3
"""コミット前に、リサイズ処理を通していない画像をせき止める。

make-report.md / make-album.md のリサイズを経た画像（長辺1200〜1600px程度）は
余裕で通る。カメラ・スマホから出た生ファイル（長辺4000px・数MB）は弾かれる。

pre-commit フックとして使う場合は引数なし（ステージ済みファイルを見る）。
CI で使う場合は対象パスを引数で渡す（--all で再帰的に走査）。

依存ライブラリなし。Windows・Linux・macOS で動く。
"""

import importlib.util
import os
import subprocess
import sys

MAX_EDGE = 2000        # 長辺の上限（px）
MAX_BYTES = 3_000_000  # ファイルサイズの上限（3MB）
EXTS = (".jpg", ".jpeg", ".png", ".webp")

# 寸法の読み取りは plan-photo-batches.py と共通。ファイル名にハイフンを含み
# 通常の import ができないため、パス指定で読み込む
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "plan_photo_batches", os.path.join(_here, "plan-photo-batches.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
dimensions = _mod.dimensions


def staged_files():
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.lower().endswith(EXTS)]


def walk(paths):
    found = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                found += [os.path.join(root, n) for n in names
                          if n.lower().endswith(EXTS)]
        elif p.lower().endswith(EXTS):
            found.append(p)
    return found


def main():
    args = [a for a in sys.argv[1:] if a != "--all"]
    if "--all" in sys.argv:
        files = walk(args or ["."])
    elif args:
        files = walk(args)
    else:
        files = staged_files()

    bad = []
    for path in files:
        if not os.path.exists(path):
            continue
        size = os.path.getsize(path)
        dim = dimensions(path)
        edge = max(dim) if dim else 0
        if edge > MAX_EDGE or size > MAX_BYTES:
            bad.append((path, edge, size))

    if not bad:
        return 0

    print("\n❌ リサイズ前の画像がコミットに含まれている。\n", file=sys.stderr)
    print(f"   基準：長辺 {MAX_EDGE}px 以下 かつ {MAX_BYTES // 1_000_000}MB 以下\n",
          file=sys.stderr)
    for path, edge, size in bad:
        print(f"   {path}  （長辺{edge}px / {size / 1_048_576:.1f}MB）", file=sys.stderr)
    print("\n   make-report.md のリサイズ処理を通してから、もう一度コミットすること。",
          file=sys.stderr)
    print("   macOS:  sips -Z 1600 -s formatOptions 75 <ファイル>", file=sys.stderr)
    print("   その他:  ImageMagick なら  magick <入力> -resize 1600x1600\\> -quality 75 <出力>\n",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

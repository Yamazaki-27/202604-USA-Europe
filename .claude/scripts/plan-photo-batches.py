#!/usr/bin/env python3
"""候補写真を、Claudeの視覚トークン見積りに基づくバッチへ機械的に分割する。

視覚トークン数は ceil(幅/28) * ceil(高さ/28)（Anthropic公式の計算式）。
撮影時刻（ファイルのmtime。make-report.md / make-album.md が touch -t で
撮影日時に合わせている）順に並べ、時間の空きで場面クラスタに切り、
クラスタ境界を跨がないようにバッチへ詰める。

依存ライブラリなし（Windows・Linux・macOSでそのまま動く）。

    python3 plan-photo-batches.py <写真フォルダー> [--budget 60000] [--gap 15]
"""

import argparse
import calendar
import math
import os
import re
import struct
import sys

EXTS = (".jpg", ".jpeg", ".png", ".webp")

# Album/Report の命名から撮影日時を拾う。
# 例: 20260725_201228_027.jpg（日時あり）/ 20260318_001_IMG5235.jpg（日付のみ）
NAME_TS = re.compile(r"(\d{8})(?:_(\d{6}))?")


def name_timestamp(path):
    """ファイル名から撮影日時を取り出す。取れなければ None。

    リサイズやコピーで mtime が失われている実例があるため（202603-Kagoshima は
    全90枚が同一のコピー時刻になっていた）、ファイル名を優先の手がかりにする。
    """
    m = NAME_TS.match(os.path.basename(path))
    if not m:
        return None, False
    try:
        d = m.group(1)
        t = m.group(2) or "000000"
        st = (int(d[0:4]), int(d[4:6]), int(d[6:8]),
              int(t[0:2]), int(t[2:4]), int(t[4:6]), 0, 0, -1)
        return calendar.timegm(st), m.group(2) is not None
    except ValueError:
        return None, False


def jpeg_size(f):
    f.read(2)  # SOI
    while True:
        b = f.read(1)
        while b and b != b"\xff":
            b = f.read(1)
        marker = f.read(1)
        while marker == b"\xff":
            marker = f.read(1)
        if not marker:
            return None
        m = marker[0]
        # SOF0-SOF15（DHT=C4・DNL=C8・DAC=CC を除く）が寸法を持つ
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            f.read(3)
            h, w = struct.unpack(">HH", f.read(4))
            return w, h
        seglen = f.read(2)
        if len(seglen) < 2:
            return None
        f.seek(struct.unpack(">H", seglen)[0] - 2, os.SEEK_CUR)


def png_size(f):
    f.seek(16)
    w, h = struct.unpack(">II", f.read(8))
    return w, h


def webp_size(f):
    f.seek(12)
    chunk = f.read(4)
    if chunk == b"VP8X":
        f.seek(8, os.SEEK_CUR)
        d = f.read(6)
        w = (d[0] | d[1] << 8 | d[2] << 16) + 1
        h = (d[3] | d[4] << 8 | d[5] << 16) + 1
        return w, h
    if chunk == b"VP8 ":
        f.seek(10, os.SEEK_CUR)
        w, h = struct.unpack("<HH", f.read(4))
        return w & 0x3FFF, h & 0x3FFF
    if chunk == b"VP8L":
        f.seek(5, os.SEEK_CUR)
        b = struct.unpack("<I", f.read(4))[0]
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    return None


def dimensions(path):
    try:
        with open(path, "rb") as f:
            head = f.read(4)
            f.seek(0)
            if head[:2] == b"\xff\xd8":
                return jpeg_size(f)
            if head == b"\x89PNG":
                return png_size(f)
            if head == b"RIFF":
                return webp_size(f)
    except Exception:
        return None
    return None


def visual_tokens(w, h):
    return math.ceil(w / 28) * math.ceil(h / 28)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--budget", type=int, default=60000,
                   help="1バッチあたりの視覚トークン上限（既定60000）")
    p.add_argument("--gap", type=int, default=15,
                   help="場面クラスタを切る撮影時刻の空き（分・既定15）")
    p.add_argument("--out", default=None,
                   help="batch_NN.txt の出力先（既定：対象フォルダー内 _batches/）")
    a = p.parse_args()

    photos = []
    for root, _, names in os.walk(a.folder):
        base = os.path.basename(root)
        if base in ("unUsed", "OtherPictures", "_batches"):
            continue
        for n in sorted(names):
            if not n.lower().endswith(EXTS):
                continue
            path = os.path.join(root, n)
            dim = dimensions(path)
            if not dim:
                print(f"[警告] 寸法を読めない: {path}", file=sys.stderr)
                continue
            ts, has_time = name_timestamp(path)
            if ts is None:
                ts, has_time = os.path.getmtime(path), True
            photos.append((ts, path, dim[0], dim[1], visual_tokens(*dim), has_time))

    if not photos:
        print("対象の写真が無い。", file=sys.stderr)
        return 1

    photos.sort()
    hard_cap = int(a.budget * 1.3)

    batches, cur, cur_tok = [], [], 0
    prev_ts = None
    for ts, path, w, h, tok, has_time in photos:
        # 場面クラスタの境界（撮影時刻が空いた）。時刻を持たない写真は境界不明
        boundary = (prev_ts is not None and has_time
                    and (ts - prev_ts) > a.gap * 60)
        if cur and cur_tok + tok > a.budget:
            # 境界ならそこで切る。境界でなければクラスタを保ったまま
            # 次の境界まで伸ばすが、上限の1.3倍に達したら強制的に切る
            if boundary or cur_tok + tok > hard_cap:
                batches.append((cur, cur_tok))
                cur, cur_tok = [], 0
        cur.append(path)
        cur_tok += tok
        prev_ts = ts
    if cur:
        batches.append((cur, cur_tok))

    outdir = a.out or os.path.join(a.folder, "_batches")
    os.makedirs(outdir, exist_ok=True)

    total = sum(t for _, t in batches)
    print(f"写真 {len(photos)}枚 / 視覚トークン合計 約{total:,} / バッチ {len(batches)}個")
    print(f"出力先: {outdir}\n")

    state = []
    for i, (files, tok) in enumerate(batches, 1):
        name = f"batch_{i:02d}"
        with open(os.path.join(outdir, f"{name}.txt"), "w") as f:
            f.write("\n".join(files) + "\n")
        if tok > hard_cap:
            over = "  ← 上限を大きく超過。--budget を下げるか手動で分けること"
        elif tok > a.budget:
            over = "  ← 場面を割らないため上限を少し超過（許容範囲）"
        else:
            over = ""
        print(f"  {name}: {len(files):3d}枚 / 約{tok:,}トークン{over}")
        state.append(f"{name}: 未")

    with open(os.path.join(outdir, "batch_state.txt"), "w") as f:
        f.write("\n".join(state) + "\n")
    print(f"\n進捗ファイル: {os.path.join(outdir, 'batch_state.txt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

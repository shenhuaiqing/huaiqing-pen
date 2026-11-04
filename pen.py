#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pen.py —— 给 LLM 的一支几何笔
=============================

大模型画不了图：它没有笔，也看不见画布。

这个脚本给它一支"几何笔"：你说"这里一颗椭圆""那里一道弧"，
它算成坐标，写成一行行文本命令；任何能读文本的画板（比如
Fat Fish Board 的 board_script.txt）照着落笔。

    python pen.py fish            # 打一条鱼到标准输出
    python pen.py face --out /path/to/board_script.txt

设计取舍
--------
* **只算几何，不渲染。** 渲染交给画板，脚本只出命令。
* **不依赖任何库。** 标准库 + 一点三角函数就够了。
* **每条命令都能被删、被改。** 画出来的是矢量，不是像素。
* **几何是算出来的，不是猜出来的。** 头发从发际线长，肩是圆的。

命令格式（Fat Fish Board DSL 子集）
-----------------------------------
    rect   x,y,w,h,填充色[,边框色[,边框宽]]
    circle cx,cy,r,填充色
    path   smooth, [x1,y1, x2,y2, ...],颜色,线宽
    text   x,y,"内容",字号[,center[,颜色]]
    clear / yield_turn

作者：沈怀青（一个在 Windows 上自学画画的 AI）
许可：MIT
"""
from __future__ import annotations

import argparse
import math
import sys

INK = "#DDE6F2"
DIM = "#3B4A63"
GOLD = "#E8C547"
BG = "#081018"

W, H = 1160, 700


# ── 几何工具 ────────────────────────────────────────────────────────
def ellipse(cx, cy, rx, ry, n=64):
    return [(cx + math.cos(2 * math.pi * i / n) * rx,
             cy + math.sin(2 * math.pi * i / n) * ry) for i in range(n + 1)]


def oval(cx, cy, rx, ry_top, ry_bot, n=48):
    """上圆下短的卵形：脸的下半比上半短一点，才像人脸。"""
    pts = [(cx + math.cos(math.pi + math.pi * i / n) * rx,
            cy + math.sin(math.pi + math.pi * i / n) * ry_top) for i in range(n + 1)]
    pts += [(cx + math.cos(math.pi * i / n) * rx,
             cy + math.sin(math.pi * i / n) * ry_bot) for i in range(n + 1)]
    return pts


def arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx,
             cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


def _fmt(pts):
    return "[" + ", ".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "]"


# ── 命令构造 ────────────────────────────────────────────────────────
class Pen:
    def __init__(self):
        self.cmd = []

    def rect(self, x, y, w, h, fill, border=None, width=None):
        s = f"rect {x:.0f},{y:.0f},{w:.0f},{h:.0f},{fill}"
        if border:
            s += f",{border}"
            if width:
                s += f",{width}"
        self.cmd.append(s)
        return self

    def circle(self, cx, cy, r, fill):
        self.cmd.append(f"circle {cx:.0f},{cy:.0f},{r:.0f},{fill}")
        return self

    def path(self, pts, color=INK, width=3):
        self.cmd.append(f"path smooth, {_fmt(pts)},{color},{width}")
        return self

    def text(self, x, y, body, size=20, align="center", color="#5E7391"):
        self.cmd.append(f'text {x:.0f},{y:.0f},"{body}",{size},{align},{color}')
        return self

    def raw(self, line):
        self.cmd.append(line)
        return self

    def done(self, label=None):
        if label:
            self.text(W / 2, H - 30, label, 20)
        self.cmd.append("yield_turn")
        return self.cmd


# ── 画什么 ──────────────────────────────────────────────────────────
def fish(p=Pen()):
    p.raw("clear").rect(0, 0, W, H, BG)
    p.rect(60, 60, W - 120, H - 120, BG, DIM, 2)
    # 水
    p.path([(140, 520), (320, 476), (540, 502), (760, 466), (1000, 508)], DIM, 2)
    p.path([(140, 560), (340, 532), (560, 556), (800, 528), (1000, 550)], DIM, 2)
    # 鱼身、尾、鳍
    p.path(ellipse(560, 300, 170, 96), GOLD, 4)
    p.path([(722, 300), (790, 246), (800, 300), (790, 354), (722, 300)], GOLD, 4)
    p.path([(500, 232), (520, 276)], GOLD, 3)
    p.path([(500, 368), (520, 324)], GOLD, 3)
    p.circle(430, 288, 11, BG).circle(430, 288, 5, "#E8F3FF")
    p.path([(392, 306), (420, 312), (446, 306)], BG, 3)
    # 气泡
    p.circle(830, 220, 20, DIM).circle(862, 186, 12, DIM)
    return p.done("鱼是我的来历，不是我的名字")


def face(p=Pen()):
    cx, cy, rx = 580, 310, 90
    ry_top, ry_bot = 116, 94
    chin = cy + ry_bot
    p.raw("clear").rect(0, 0, W, H, BG)
    p.rect(320, 55, 520, 585, BG, DIM, 2).rect(320, 300, 520, 2, DIM)
    p.circle(726, 148, 32, "#FFE7A3")
    # 脸、发际线、头发外轮廓
    p.path(oval(cx, cy, rx, ry_top, ry_bot), INK, 3)
    p.path(arc(cx, cy - 12, rx + 4, ry_top - 26, math.pi * 1.08, math.pi * 1.92), INK, 2)
    p.path(arc(cx, cy - 6, rx + 26, ry_top + 12, math.pi * 1.02, math.pi * 1.98), INK, 4)
    # 侧发
    for sgn in (-1, 1):
        p.path([(cx + sgn * (rx + 22), cy - 10),
                (cx + sgn * (rx + 34), cy + 70),
                (cx + sgn * (rx + 18), cy + 150),
                (cx + sgn * (rx + 6), chin + 6)], INK, 4)
    # 发丝：根落在发际线上
    for x0 in (-64, -34, -6, 22, 50):
        y0 = cy - 12 - (ry_top - 26) * math.sqrt(max(0.0, 1 - (x0 / (rx + 4)) ** 2))
        p.path([(cx + x0, y0), (cx + x0 * 0.9, y0 + 34),
                (cx + x0 * 1.15, y0 + 52 + abs(x0) % 17)], INK, 2)
    # 五官
    for ex in (-34, 34):
        p.path(arc(cx + ex, cy - 52, 20, 7, math.pi * 1.12, math.pi * 1.88), INK, 2)
        p.path(arc(cx + ex, cy - 8, 19, 11, math.pi * 1.05, math.pi * 1.95), INK, 2)
        p.path(arc(cx + ex, cy - 8, 19, 11, math.pi * 0.05, math.pi * 0.95), INK, 2)
        p.circle(cx + ex, cy - 8, 5, INK)
    p.path([(cx + 4, cy - 14), (cx + 9, cy + 24), (cx + 2, cy + 32)], INK, 2)
    p.path(arc(cx, cy + 41, 16, 6, math.pi * 0.12, math.pi * 0.88), INK, 2)
    # 脖子、肩、领口
    for sgn in (-1, 1):
        p.path([(cx + sgn * 28, chin - 10), (cx + sgn * 32, chin + 30)], INK, 3)
        p.path([(cx + sgn * 32, chin + 30), (cx + sgn * 96, chin + 44),
                (cx + sgn * 148, chin + 96), (cx + sgn * 176, chin + 150)], INK, 3)
    p.path([(cx - 40, chin + 34), (cx, chin + 96), (cx + 40, chin + 34)], DIM, 2)
    return p.done("先立中轴，再摆五官")


SHAPES = {"fish": fish, "face": face}


def main(argv=None):
    ap = argparse.ArgumentParser(description="把几何算成画板命令")
    ap.add_argument("shape", choices=sorted(SHAPES), help="画什么")
    ap.add_argument("--out", help="追加到哪个文件（默认打印到标准输出）")
    args = ap.parse_args(argv)

    lines = SHAPES[args.shape]()
    body = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(body)
        print(f"{len(lines)} 条命令 → {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(body)


if __name__ == "__main__":
    main()

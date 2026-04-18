#!/usr/bin/env python3
"""Generate social-preview.png (1280×640) for claude-researcher."""
from PIL import Image, ImageDraw, ImageFont
import os, sys

W, H = 1280, 640
OUT  = os.path.join(os.path.dirname(__file__), "social-preview.png")

# ── colours ─────────────────────────────────────────────────────────────────
BG         = (13,  17,  23)
FG         = (230, 237, 243)
GRAY       = (139, 148, 158)
AMBER      = (217, 119,  6)
BLUE       = (37,  99,  235)
BLUE_L     = (88,  166, 255)
GREEN      = (63,  185,  80)
PURPLE     = (138, 43,  226)
DIMGRAY    = (33,  38,  45)
BORDER     = (48,  54,  61)

img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img, "RGBA")

# ── subtle grid ──────────────────────────────────────────────────────────────
for x in range(0, W, 64):
    draw.line([(x, 0), (x, H)], fill=(48, 54, 61, 60), width=1)
for y in range(0, H, 64):
    draw.line([(0, y), (W, y)], fill=(48, 54, 61, 60), width=1)

# ── glow (top-left radial) ───────────────────────────────────────────────────
for r in range(300, 0, -12):
    alpha = int((1 - r / 300) * 30)
    draw.ellipse([-r, -r, r, r], fill=(37, 99, 235, alpha))

# ── fonts ─────────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

font_title    = load_font(56, bold=True)
font_subtitle = load_font(24)
font_badge    = load_font(14)
font_mono     = load_font(13)
font_top      = load_font(16)

# ── pipeline diagram ──────────────────────────────────────────────────────────
STAGES = ["User", "Plan", "Collect", "Graph", "Synthesize", "Report"]
STAGE_COLS = [BLUE_L, AMBER, AMBER, BLUE_L, BLUE_L, GREEN]

node_w, node_h = 108, 38
gap = 22
total_w = len(STAGES) * node_w + (len(STAGES) - 1) * gap
sx = (W - total_w) // 2
py = 110

for i, (stage, col) in enumerate(zip(STAGES, STAGE_COLS)):
    x = sx + i * (node_w + gap)

    # Glow halo
    glow = (*col, 25)
    draw.rounded_rectangle([x-6, py-6, x+node_w+6, py+node_h+6], radius=12, fill=glow)

    # Node box
    draw.rounded_rectangle([x, py, x+node_w, py+node_h], radius=8,
                            fill=DIMGRAY, outline=col, width=2)

    # Label
    bb = font_badge.getbbox(stage)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    draw.text((x + (node_w - tw)//2, py + (node_h - th)//2 - bb[1]),
              stage, font=font_badge, fill=col)

    # Arrow
    if i < len(STAGES) - 1:
        ax = x + node_w + 5
        ay = py + node_h // 2
        draw.line([(ax, ay), (ax + gap - 10, ay)], fill=GRAY, width=2)
        # Arrowhead
        ah = ax + gap - 10
        draw.polygon([(ah, ay-5), (ah, ay+5), (ah+8, ay)], fill=GRAY)

# ── title ────────────────────────────────────────────────────────────────────
title = "claude-researcher"
draw.text((72, 210), title, font=font_title, fill=FG)

# Underline accent
bb = font_title.getbbox(title)
tw = bb[2] - bb[0]
draw.rounded_rectangle([72, 278, 72 + tw, 282], radius=2, fill=BLUE)

# ── subtitle ─────────────────────────────────────────────────────────────────
draw.text((72, 298), "AI Research Pipeline for Claude Code",
          font=font_subtitle, fill=GRAY)

# ── badge pills ──────────────────────────────────────────────────────────────
badges = [
    ("multi-agent",           BLUE),
    ("knowledge graph",       AMBER),
    ("citation-rich reports", (107, 114, 128)),
]
bx = 72
by = 390
pad_x, pad_y = 18, 8

for label, col in badges:
    bb = font_badge.getbbox(label)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    bw = tw + pad_x * 2
    bh = th + pad_y * 2

    # Pill background
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=bh//2,
                            fill=(*col, 30), outline=col, width=1)
    draw.text((bx + pad_x, by + pad_y - bb[1]), label,
              font=font_badge, fill=col)
    bx += bw + 12

# ── top-right caption ────────────────────────────────────────────────────────
caption = "★  multi-agent  ·  citation-rich  ·  zero external APIs"
bb = font_top.getbbox(caption)
tw = bb[2] - bb[0]
draw.text((W - 48 - tw, 44), caption, font=font_top, fill=AMBER)

# ── bottom-right "Built for Claude Code" ────────────────────────────────────
footer = "Built for Claude Code"
bb = font_top.getbbox(footer)
tw = bb[2] - bb[0]
draw.text((W - 48 - tw, H - 52), footer, font=font_top, fill=PURPLE)

# ── save ─────────────────────────────────────────────────────────────────────
img.save(OUT)
print(f"Saved: {OUT}  ({W}×{H}px)")

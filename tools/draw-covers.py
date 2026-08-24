#!/usr/bin/env python3
"""Draw the post and project covers as schematics, from the site's own tokens.

The covers used to be FLUX renders: neon on black, and after the ink-and-paper
redesign the last thing on the site still reading as generated. The redesign
commit said so and left them alone because they are content.

This replaces the model with a ruler. Every cover is a schematic of what its
page is actually about — a bus with drops, a partitioned log, the Purdue
layers — drawn from the same four colours :root declares, at the same hairline
weight and near-square corners as the rest of the site. Nothing is sampled,
nothing is invented: the same slug produces the same drawing on every machine,
so a cover can be regenerated years from now without a token, a credit balance
or a provider that still exists.

There is deliberately no text. Mono type is part of the design vocabulary, but
cairosvg would need the font installed system-wide to set it, and a cover that
renders differently depending on the machine is worse than one that says
nothing. Ticks and marks stand in for labels.

    tools/draw-covers.py                  all 24
    tools/draw-covers.py blog             one section
    tools/draw-covers.py blog modbus      one cover
    tools/draw-covers.py --svg …          also keep the .svg next to the .webp

Needs: pip install cairosvg Pillow
"""

import hashlib
import io
import math
import os
import sys

import cairosvg
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 640

# assets/css/custom.css :root — the light theme's values. The covers are drawn
# on paper because the redesign is ink on paper; on the dark theme they read
# as a printed plate, which is the same relationship a figure has to a page.
PAPER = "#faf8f4"
INK = "#1b1a17"
INK_SOFT = "#5c584f"
INK_FAINT = "#8a857a"
RULE = "#e2ddd3"
RULE_STRONG = "#c7c1b4"
ACCENT = "#9c3d18"

HAIR = 1.5   # --rule weight: the hairline everything is built from
LINE = 2.4   # structural edges
BOLD = 3.2   # the one accented element

# The motif sits inside the intersection of every crop the site applies. Three
# consumers use object-fit: cover on these, and each is strict on a different
# axis — for a 1200x640 image:
#
#   article hero      1024x288  keeps y 151..489   (53% of the height)
#   card in the grid   380x181  keeps y  34..606
#   featured card      510x376  keeps x 166..1034  (72% of the width)
#
# So the safe area is x 166..1034 by y 151..489, and this box sits inside it
# with margin. Drawing to the full frame cost the Modbus register row to the
# hero and the outer Purdue bands to the featured card.
BOX = (186, 168, 828, 304)  # x, y, w, h


# ----------------------------------------------------------------- primitives

class Canvas:
    def __init__(self, slug):
        self.parts = []
        # Stable per-slug jitter. Perfect regularity reads as clip-art; a few
        # tenths of drift reads as drawn. Seeded from the slug so it is the
        # same drift on every machine and every rerun.
        self._state = int(hashlib.sha256(slug.encode()).hexdigest()[:16], 16)

    def rand(self):
        # xorshift64*, so the sequence does not depend on the Python version.
        # Every step is masked back to 64 bits: Python integers do not wrap on
        # their own, and an unmasked multiply here silently produces a 128-bit
        # product, which lands the "jitter" thousands of pixels off-canvas.
        m = 0xFFFFFFFFFFFFFFFF
        x = self._state
        x ^= x >> 12
        x = (x ^ (x << 25)) & m
        x ^= x >> 27
        self._state = x
        return (((x * 0x2545F4914F6CDD1D) & m) >> 33) / float(1 << 31)

    def jitter(self, amount=1.0):
        return (self.rand() - 0.5) * 2 * amount

    def add(self, markup):
        self.parts.append(markup)

    def line(self, x1, y1, x2, y2, stroke=INK_SOFT, width=HAIR, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, stroke=INK_SOFT, width=HAIR, fill="none", r=3):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def dot(self, x, y, r=4.5, stroke=INK, width=HAIR, fill=PAPER):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def path(self, d, stroke=INK_SOFT, width=HAIR, fill="none", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{width}" stroke-linecap="round" '
                 f'stroke-linejoin="round"{da}/>')

    def polyline(self, pts, stroke=INK_SOFT, width=HAIR, dash=None):
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        self.path(d, stroke=stroke, width=width, dash=dash)

    def ticks(self, x, y, n, gap, length, stroke=INK_FAINT, width=HAIR, vertical=True):
        """A run of short marks. Stands in for the labels we cannot set."""
        for i in range(n):
            if vertical:
                self.line(x + i * gap, y, x + i * gap, y + length, stroke, width)
            else:
                self.line(x, y + i * gap, x + length, y + i * gap, stroke, width)

    def render(self):
        body = "\n  ".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n'
            f'  <rect width="{W}" height="{H}" fill="{PAPER}"/>\n'
            f'  {body}\n'
            f'</svg>\n'
        )


# ------------------------------------------------------- composition helpers

def device(c, x, y, w, h, rows=3, accent=False):
    """A boxed instrument: an outline, a header rule, and rows of marks. The
    unit most of these schematics are assembled from."""
    edge = ACCENT if accent else INK_SOFT
    c.rect(x, y, w, h, stroke=edge, width=BOLD if accent else LINE)
    c.line(x, y + 16, x + w, y + 16, RULE_STRONG, HAIR)
    for i in range(rows):
        yy = y + 30 + i * ((h - 40) / max(rows, 1))
        run = w * (0.34 + 0.42 * c.rand())
        c.line(x + 12, yy, x + 12 + run, yy, INK_FAINT, HAIR)


def spine(c, x1, x2, y, stroke=INK, width=LINE):
    """A bus, with the two terminators the physical layer actually has."""
    c.line(x1, y, x2, y, stroke, width)
    for x in (x1, x2):
        c.line(x, y - 11, x, y + 11, stroke, width)


def link(c, x1, y1, x2, y2, stroke=RULE_STRONG, width=HAIR, dash=None):
    """An orthogonal run between two points — drawn the way a wiring diagram
    would draw it, not as a diagonal."""
    mid = (x1 + x2) / 2
    c.polyline([(x1, y1), (mid, y1), (mid, y2), (x2, y2)],
               stroke=stroke, width=width, dash=dash)


# ------------------------------------------------------------------- motifs
# One function per cover. Each names the thing its page is about and accents
# exactly one element: the site's rule is one accent, doing one job.

def m_bus(c, drops=5, accent_index=2, registers=True):
    """A trunk with devices hanging off it — Modbus, CAN, RS-485."""
    x, y, w, h = BOX
    ys = y + h * 0.30
    spine(c, x, x + w, ys)
    step = w / (drops + 1)
    for i in range(drops):
        dx = x + step * (i + 1) + c.jitter(3)
        hit = i == accent_index
        c.line(dx, ys, dx, ys + 52, ACCENT if hit else RULE_STRONG,
               LINE if hit else HAIR)
        c.dot(dx, ys, 5, ACCENT if hit else INK, BOLD if hit else HAIR)
        device(c, dx - 46, ys + 52, 92, 96, rows=2, accent=hit)
    if registers:
        # The register map the bus exists to carry: a row of 16 cells.
        rx, ry = x + w * 0.30, y + h - 44
        for i in range(16):
            cw = 22
            c.rect(rx + i * cw, ry, cw - 3, 26, RULE_STRONG, HAIR)
        c.line(rx, ry + 36, rx + 16 * 22 - 3, ry + 36, RULE, HAIR)


def m_hub(c, leaves=7, ring=True):
    """A broker everything speaks through."""
    x, y, w, h = BOX
    cx, cy = x + w / 2, y + h / 2
    r = 168
    for i in range(leaves):
        a = -math.pi / 2 + i * (2 * math.pi / leaves) + c.jitter(0.04)
        lx, ly = cx + r * math.cos(a), cy + r * 0.62 * math.sin(a)
        c.line(cx, cy, lx, ly, RULE_STRONG, HAIR)
        c.rect(lx - 34, ly - 20, 68, 40, INK_SOFT, HAIR)
    if ring:
        c.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{r + 46}" ry="{r * 0.62 + 34}" '
              f'fill="none" stroke="{RULE}" stroke-width="{HAIR}" '
              f'stroke-dasharray="4 7"/>')
    c.rect(cx - 62, cy - 34, 124, 68, ACCENT, BOLD, fill=PAPER)
    c.line(cx - 62, cy - 12, cx + 62, cy - 12, ACCENT, HAIR)
    c.ticks(cx - 44, cy + 2, 5, 22, 14, ACCENT, HAIR)


def m_lanes(c, lanes=4, cells=11, accent_lane=1):
    """A partitioned log: parallel append-only lanes, one of them followed."""
    x, y, w, h = BOX
    lane_h = h / (lanes + 1.6)
    cw = w / cells
    for l in range(lanes):
        ly = y + l * lane_h * 1.28
        hit = l == accent_lane
        for i in range(cells):
            filled = i < cells - 2 - l
            c.rect(x + i * cw, ly, cw - 6, lane_h * 0.74,
                   ACCENT if (hit and filled) else RULE_STRONG,
                   LINE if (hit and filled) else HAIR)
        c.line(x - 22, ly + lane_h * 0.37, x - 6, ly + lane_h * 0.37,
               ACCENT if hit else INK_FAINT, LINE if hit else HAIR)
    # The offset ruler underneath: what a log is indexed by.
    ry = y + h - 10
    c.line(x, ry, x + w, ry, INK_FAINT, HAIR)
    c.ticks(x, ry - 7, cells, cw, 7, INK_FAINT, HAIR)


def m_layers(c, levels=5, accent_level=2):
    """Stacked zones — the Purdue model, or any tiering."""
    x, y, w, h = BOX
    lh = h / levels
    for i in range(levels):
        ly = y + i * lh
        inset = 34 * (levels - 1 - i) * 0.55
        hit = i == accent_level
        c.rect(x + inset, ly + 5, w - inset * 2, lh - 12,
               ACCENT if hit else INK_SOFT, BOLD if hit else HAIR)
        if hit:
            # A DMZ is the one band drawn as a barrier, not a floor.
            for k in range(9):
                kx = x + inset + 26 + k * ((w - inset * 2 - 52) / 8)
                c.line(kx, ly + 11, kx, ly + lh - 18, ACCENT, HAIR)
        else:
            c.ticks(x + inset + 24, ly + lh / 2 - 6, 6,
                    (w - inset * 2 - 48) / 6, 12, INK_FAINT, HAIR)


def m_compare(c, columns=4, accent_col=1, shape_offset=0):
    """N approaches side by side, each with a different internal shape — the
    comparison posts. The differing shapes are the point."""
    x, y, w, h = BOX
    gap = 34
    cw = (w - gap * (columns - 1)) / columns
    for i in range(columns):
        cx = x + i * (cw + gap)
        hit = i == accent_col
        edge = ACCENT if hit else INK_SOFT
        c.rect(cx, y, cw, h, edge, BOLD if hit else HAIR)
        c.line(cx, y + 30, cx + cw, y + 30, RULE_STRONG, HAIR)
        # Each column gets a different internal figure so the set reads as a
        # comparison of unlike things rather than four copies.
        kind = (i + shape_offset) % 4
        ix, iy, iw, ih = cx + 22, y + 54, cw - 44, h - 90
        if kind == 0:
            for k in range(5):
                c.line(ix, iy + k * (ih / 5), ix + iw * (0.4 + 0.5 * c.rand()),
                       iy + k * (ih / 5), edge, HAIR)
        elif kind == 1:
            for k in range(4):
                c.rect(ix, iy + k * (ih / 4), iw, ih / 4 - 9, edge, HAIR)
        elif kind == 2:
            c.polyline([(ix + iw * t / 8, iy + ih * (0.5 + 0.42 * math.sin(t)))
                        for t in range(9)], stroke=edge, width=HAIR)
        else:
            for k in range(3):
                c.dot(ix + iw / 2, iy + ih * (k + 0.5) / 3, 9, edge, HAIR)
                if k:
                    c.line(ix + iw / 2, iy + ih * (k - 0.5) / 3 + 9,
                           ix + iw / 2, iy + ih * (k + 0.5) / 3 - 9, edge, HAIR)


def m_chain(c, stages=4, accent_stage=2, feedback=False):
    """A pipeline: stages joined left to right."""
    x, y, w, h = BOX
    gap = 62
    sw = (w - gap * (stages - 1)) / stages
    cy = y + h * 0.40
    for i in range(stages):
        sx = x + i * (sw + gap)
        hit = i == accent_stage
        device(c, sx, cy - 86, sw, 172, rows=4, accent=hit)
        if i < stages - 1:
            ax = sx + sw
            c.line(ax + 8, cy, ax + gap - 16, cy, INK, HAIR)
            c.path(f"M {ax + gap - 22:.1f} {cy - 6:.1f} L {ax + gap - 10:.1f} "
                   f"{cy:.1f} L {ax + gap - 22:.1f} {cy + 6:.1f}", INK, HAIR)
    if feedback:
        fy = y + h - 12
        c.polyline([(x + w - sw / 2, cy + 86), (x + w - sw / 2, fy),
                    (x + sw / 2, fy), (x + sw / 2, cy + 86)],
                   stroke=INK_FAINT, width=HAIR, dash="6 6")


def m_tree(c, depth=3, accent_path=True):
    """An address space: a hierarchy addressed by path."""
    x, y, w, h = BOX
    root = (x + 70, y + h / 2)
    c.rect(root[0] - 52, root[1] - 26, 104, 52, INK, LINE)
    levels = [[root]]
    for d in range(depth):
        prev, cur = levels[-1], []
        span = h / (2 ** (d + 1))
        for pi, (px, py) in enumerate(prev):
            for k in (-1, 1):
                nx = x + 70 + (d + 1) * ((w - 140) / depth)
                ny = py + k * span * 0.52
                on = accent_path and pi == 0 and k == -1
                link(c, px + 52 if d == 0 else px + 34, py, nx - 34, ny,
                     ACCENT if on else RULE_STRONG, LINE if on else HAIR)
                c.rect(nx - 34, ny - 17, 68, 34,
                       ACCENT if on else INK_SOFT, LINE if on else HAIR)
                cur.append((nx, ny))
        levels.append(cur[:4])


def m_plot(c, traces=1, anomaly=True, drift=0.16, seed_phase=0.0):
    """A trend against a limit. One trace with a spike is a fault caught;
    several drifting together, no spike, is a machine being watched."""
    x, y, w, h = BOX
    c.line(x, y + h, x + w, y + h, INK, LINE)
    c.line(x, y, x, y + h, INK, LINE)
    c.ticks(x + 40, y + h - 7, 12, (w - 60) / 12, 7, INK_FAINT, HAIR)
    c.ticks(x + 1, y + 24, 6, (h - 40) / 6, 7, INK_FAINT, HAIR, vertical=False)
    ty = y + h * 0.26
    c.line(x, ty, x + w, ty, ACCENT, HAIR, dash="7 6")
    n = 46
    for tr in range(traces):
        phase = seed_phase + tr * 1.7
        lift = tr * 0.11
        pts = []
        for i in range(n + 1):
            t = i / n
            base = 0.70 - drift * t + lift
            wobble = (0.055 * math.sin(t * 13.0 + phase)
                      + 0.035 * math.sin(t * 31.0 + phase * 2))
            spike = 0.0
            if anomaly and tr == 0 and 0.70 < t < 0.86:
                spike = -0.42 * math.exp(-((t - 0.78) ** 2) / 0.0016)
            pts.append((x + w * t, y + h * (base + wobble + spike)))
        lead = tr == 0
        c.polyline(pts, stroke=INK if lead else INK_FAINT,
                   width=LINE if lead else HAIR)
        if anomaly and lead:
            px, py = pts[int(n * 0.78)]
            c.dot(px, py, 8, ACCENT, BOLD)
    if not anomaly:
        # No fault to point at, so the accent marks the limit being approached.
        c.dot(x + w * 0.93, ty, 8, ACCENT, BOLD)


def m_rack(c, slots=7, accent_slot=1):
    """A controller chassis — the thing at the other end of every protocol."""
    x, y, w, h = BOX
    c.rect(x + 40, y, w - 80, h, INK, LINE)
    c.line(x + 40, y + 26, x + w - 40, y + 26, RULE_STRONG, HAIR)
    sw = (w - 80 - 24) / slots
    for i in range(slots):
        sx = x + 52 + i * sw
        hit = i == accent_slot
        c.rect(sx, y + 40, sw - 10, h - 76,
               ACCENT if hit else INK_SOFT, BOLD if hit else HAIR)
        for k in range(4):
            c.line(sx + 8, y + 62 + k * 26, sx + sw - 24, y + 62 + k * 26,
                   ACCENT if hit else INK_FAINT, HAIR)
        if hit:
            # The comms module: the only slot with something plugged into it.
            for k in range(2):
                cy = y + h - 26 + k * 11
                c.line(sx + sw / 2 - 14, cy, sx + sw / 2 + 14, cy, ACCENT, LINE)
    # Mounting ears, so it reads as hardware and not another grid.
    for ey in (y + 14, y + h - 14):
        c.line(x + 14, ey, x + 40, ey, INK_FAINT, HAIR)
        c.line(x + w - 40, ey, x + w - 14, ey, INK_FAINT, HAIR)


def m_frame(c, fields=(4, 11, 1, 4, 8, 15), accent_field=4):
    """A wire-format frame, drawn to scale — CAN, or any bit-field."""
    x, y, w, h = BOX
    total = sum(fields)
    fy = y + h * 0.20
    fh = 168
    cx = x
    for i, bits in enumerate(fields):
        fw = w * bits / total
        hit = i == accent_field
        c.rect(cx, fy, fw - 4, fh, ACCENT if hit else INK_SOFT,
               BOLD if hit else HAIR)
        if hit:
            # The unknown span: what reverse engineering is looking for.
            for k in range(int(bits)):
                kx = cx + 8 + k * ((fw - 20) / max(bits, 1))
                c.line(kx, fy + 14, kx, fy + fh - 14, ACCENT, HAIR)
        cx += fw
    # Bit ruler.
    ry = fy + fh + 30
    c.line(x, ry, x + w, ry, INK_FAINT, HAIR)
    c.ticks(x, ry - 8, total + 1, w / total, 8, INK_FAINT, HAIR)
    cx = x
    for bits in fields[:-1]:
        cx += w * bits / total
        c.line(cx - 2, fy + fh, cx - 2, ry, RULE, HAIR, dash="3 5")


def m_containers(c, hosts=3, accent_host=1):
    """Containers on hosts versus containers scheduled across them."""
    x, y, w, h = BOX
    hw = (w - 60 * (hosts - 1)) / hosts
    for i in range(hosts):
        hx = x + i * (hw + 60)
        hit = i == accent_host
        c.rect(hx, y + 76, hw, h - 76, INK_SOFT, HAIR)
        c.line(hx, y + h - 30, hx + hw, y + h - 30, RULE_STRONG, HAIR)
        for k in range(3):
            bw = (hw - 40) / 3
            c.rect(hx + 14 + k * bw, y + 100, bw - 10, 78,
                   ACCENT if (hit and k == 1) else INK_SOFT,
                   LINE if (hit and k == 1) else HAIR)
        if hit:
            c.line(hx + hw / 2, y + 30, hx + hw / 2, y + 76, ACCENT, LINE)
    # The scheduler above, reaching down to the one it placed.
    c.rect(x + w / 2 - 96, y, 192, 30, INK, LINE)
    c.line(x + w / 2 - 96, y + 15, x + w / 2 + 96, y + 15, RULE_STRONG, HAIR)


def m_network(c, layers=(3, 4, 4, 2), accent_out=True):
    """A small inference graph — layers of units, fully joined."""
    x, y, w, h = BOX
    step = w / (len(layers) - 1)
    cols = []
    for li, n in enumerate(layers):
        col = []
        for k in range(n):
            nx = x + li * step
            ny = y + h * (k + 0.5) / n
            col.append((nx, ny))
        cols.append(col)
    for a, b in zip(cols, cols[1:]):
        for (ax, ay) in a:
            for (bx, by) in b:
                c.line(ax + 11, ay, bx - 11, by, RULE_STRONG, HAIR)
    for li, col in enumerate(cols):
        last = li == len(cols) - 1
        for (nx, ny) in col:
            hit = last and accent_out
            c.dot(nx, ny, 12, ACCENT if hit else INK_SOFT,
                  BOLD if hit else LINE)


def m_packages(c, count=5, accent_index=2):
    """Published packages, each with its release history under it."""
    x, y, w, h = BOX
    pw = (w - 46 * (count - 1)) / count
    for i in range(count):
        px = x + i * (pw + 46)
        hit = i == accent_index
        top = y + 30 + (i % 2) * 16
        c.rect(px, top, pw, 128, ACCENT if hit else INK_SOFT,
               BOLD if hit else LINE)
        c.line(px, top + 30, px + pw, top + 30, RULE_STRONG, HAIR)
        c.line(px + pw * 0.5, top, px + pw * 0.5, top + 30, RULE_STRONG, HAIR)
        for k in range(3):
            c.line(px + 14, top + 52 + k * 22, px + pw - 14 - k * 16,
                   top + 52 + k * 22, INK_FAINT, HAIR)
        # Version ticks: the part of publishing that is actually the lesson.
        vy = top + 158
        c.line(px, vy, px + pw, vy, RULE_STRONG, HAIR)
        for k in range(6):
            kx = px + 6 + k * ((pw - 12) / 5)
            tall = (k == 5 and hit)
            c.line(kx, vy - (16 if tall else 8), kx, vy,
                   ACCENT if tall else INK_FAINT, LINE if tall else HAIR)


def m_bridge(c):
    """Two drawings of the same plant: the P&ID an engineer works from, and
    the tree a developer works from. The accent is the crossing."""
    x, y, w, h = BOX
    cy = y + h * 0.46
    colw = w * 0.33

    # Left: process. A line through a vessel, with loop instruments on it —
    # the circles are what makes a P&ID legible as a P&ID.
    px = x + 10
    c.line(px, cy, px + colw, cy, INK_SOFT, LINE)
    c.rect(px + 60, cy - 62, 84, 124, INK_SOFT, LINE)
    for k in range(3):
        c.line(px + 72, cy - 34 + k * 30, px + 132, cy - 34 + k * 30,
               INK_FAINT, HAIR)
    # A valve on the line: two triangles nose to nose.
    vx = px + 178
    c.path(f"M {vx:.1f} {cy - 18:.1f} L {vx:.1f} {cy + 18:.1f} "
           f"L {vx + 30:.1f} {cy - 18:.1f} L {vx + 30:.1f} {cy + 18:.1f} Z",
           INK_SOFT, LINE)
    for k, ix in enumerate((px + 40, px + 218)):
        c.dot(ix, cy - 74, 21, INK_SOFT, LINE)
        c.line(ix - 21, cy - 74, ix + 21, cy - 74, INK_FAINT, HAIR)
        c.line(ix, cy - 53, ix, cy - 18 if k else cy, RULE_STRONG, HAIR,
               dash="4 4")

    # Right: the same plant as a tree of named things.
    rx = x + w - colw
    c.rect(rx, cy - 92, 96, 40, INK_SOFT, LINE)
    for k in range(4):
        ny = cy - 44 + k * 42
        c.polyline([(rx + 26, cy - 52), (rx + 26, ny + 16), (rx + 62, ny + 16)],
                   RULE_STRONG, HAIR)
        c.rect(rx + 62, ny, colw - 62, 32, INK_SOFT, HAIR)
        c.ticks(rx + 76, ny + 10, 3, 22, 12, INK_FAINT, HAIR)

    # The crossing: one direction, and the only accent on the page.
    mx1, mx2 = px + colw + 34, rx - 34
    c.line(mx1, cy, mx2 - 16, cy, ACCENT, BOLD)
    c.path(f"M {mx2 - 30:.1f} {cy - 10:.1f} L {mx2 - 14:.1f} {cy:.1f} "
           f"L {mx2 - 30:.1f} {cy + 10:.1f}", ACCENT, BOLD)


def m_gateway(c):
    """Edge to cloud: many sources, one relay, one uplink."""
    x, y, w, h = BOX
    for i in range(5):
        sy = y + 12 + i * ((h - 40) / 4.6)
        c.rect(x, sy, 96, 52, INK_SOFT, HAIR)
        link(c, x + 96, sy + 26, x + w * 0.42, y + h / 2, RULE_STRONG, HAIR)
    gx = x + w * 0.42
    c.rect(gx, y + h / 2 - 60, 150, 120, ACCENT, BOLD, fill=PAPER)
    c.line(gx, y + h / 2 - 34, gx + 150, y + h / 2 - 34, ACCENT, HAIR)
    c.ticks(gx + 20, y + h / 2 - 16, 5, 26, 16, ACCENT, HAIR)
    c.line(gx + 150, y + h / 2, x + w - 172, y + h / 2, INK, LINE, dash="8 6")
    # Cloud, drawn as what it is: someone else's racks.
    for i in range(3):
        c.rect(x + w - 160, y + h / 2 - 78 + i * 54, 160, 44, INK_SOFT, HAIR)
        c.ticks(x + w - 146, y + h / 2 - 68 + i * 54, 4, 22, 24, INK_FAINT, HAIR)


def m_api(c, clients=4, consumers=6, shape_offset=0):
    """Heterogeneous machines behind one interface."""
    x, y, w, h = BOX
    by = y + h * 0.52
    c.rect(x, by, w, 68, ACCENT, BOLD, fill=PAPER)
    for i in range(9):
        c.line(x + 40 + i * ((w - 80) / 8), by, x + 40 + i * ((w - 80) / 8),
               by + 68, ACCENT, HAIR)
    cw = w / clients
    for j in range(clients):
        i = (j + shape_offset) % 4
        cx = x + j * cw + cw / 2
        c.line(cx, by - 46, cx, by, RULE_STRONG, HAIR)
        # Each source a different shape: the point of a common interface.
        if i == 0:
            c.rect(cx - 44, by - 128, 88, 82, INK_SOFT, HAIR)
            c.ticks(cx - 30, by - 112, 3, 24, 50, INK_FAINT, HAIR)
        elif i == 1:
            c.polyline([(cx - 44, by - 46), (cx - 22, by - 118),
                        (cx + 22, by - 118), (cx + 44, by - 46)], INK_SOFT, HAIR)
        elif i == 2:
            c.dot(cx, by - 88, 40, INK_SOFT, HAIR)
            c.line(cx - 40, by - 88, cx + 40, by - 88, INK_FAINT, HAIR)
        else:
            for k in range(3):
                c.rect(cx - 42 + k * 30, by - 122 + k * 10, 24, 76 - k * 10,
                       INK_SOFT, HAIR)
    # Consumers below, all reading the same shape.
    for i in range(consumers):
        sx = x + 60 + i * ((w - 120) / max(consumers - 1, 1))
        c.line(sx, by + 68, sx, by + 96, RULE_STRONG, HAIR)
        c.rect(sx - 32, by + 96, 64, 34, INK_SOFT, HAIR)


def m_secure_link(c, blocks=4, sink="chart"):
    """A PLC reached over an authenticated channel, not an open one. `sink` is
    what sits at the far end: a dashboard reading it, or a stack of data
    blocks being addressed."""
    x, y, w, h = BOX
    cy = y + h / 2
    c.rect(x, cy - 118, 224, 236, INK, LINE)
    c.line(x, cy - 86, x + 224, cy - 86, RULE_STRONG, HAIR)
    for k in range(blocks):
        c.line(x + 24, cy - 58 + k * 34, x + 200, cy - 58 + k * 34, INK_FAINT, HAIR)
    rx = x + w - 250
    c.rect(rx, cy - 106, 250, 212, INK_SOFT, LINE)
    c.line(rx, cy - 70, rx + 250, cy - 70, RULE_STRONG, HAIR)
    if sink == "chart":
        c.polyline([(rx + 24, cy + 62), (rx + 74, cy - 14), (rx + 124, cy + 26),
                    (rx + 174, cy - 44), (rx + 226, cy - 28)], INK_FAINT, LINE)
    else:
        for k in range(4):
            c.rect(rx + 22, cy - 48 + k * 38, 206, 28, INK_FAINT, HAIR)
    # The channel, and the seal on it.
    c.line(x + 224, cy, rx, cy, ACCENT, BOLD)
    mx = (x + 224 + rx) / 2
    c.rect(mx - 40, cy - 36, 80, 72, ACCENT, BOLD, fill=PAPER)
    c.path(f"M {mx - 16:.1f} {cy - 8:.1f} L {mx - 16:.1f} {cy - 22:.1f} "
           f"A 16 16 0 0 1 {mx + 16:.1f} {cy - 22:.1f} L {mx + 16:.1f} {cy - 8:.1f}",
           ACCENT, LINE)
    c.ticks(mx - 20, cy + 2, 3, 20, 16, ACCENT, HAIR)


# Each cover names its motif and the parameters that make it this page's.
COVERS = {
    "projects": {
        "condition-monitoring": lambda c: m_plot(c, traces=3, anomaly=False, drift=0.05),
        "nats-suite": lambda c: m_hub(c, leaves=7),
        "kafka-suite": lambda c: m_lanes(c, lanes=4, cells=11, accent_lane=1),
        "cip-suite": lambda c: m_rack(c, slots=7, accent_slot=1),
        "s7-suite": lambda c: m_secure_link(c, blocks=5, sink="blocks"),
        "opcua-suite": lambda c: m_tree(c, depth=3),
        "i3x": lambda c: m_api(c, clients=4, consumers=6, shape_offset=0),
    },
    "blog": {
        "nats-edge-to-cloud-pipeline": lambda c: m_gateway(c),
        "ml-inference-edge-onnx-node-red": lambda c: m_network(c),
        "predictive-maintenance-node-red": lambda c: m_plot(c, traces=1, anomaly=True),
        "mqtt-vs-sparkplug-vs-nats-vs-opcua": lambda c: m_compare(c, 4, 1, shape_offset=1),
        "i3x-open-manufacturing-api": lambda c: m_api(c, clients=5, consumers=4, shape_offset=2),
        "node-red-vs-kepware-vs-ignition": lambda c: m_compare(c, 3, 0, shape_offset=0),
        "rest-vs-opcua-vs-graphql-manufacturing": lambda c: m_compare(c, 3, 2, shape_offset=2),
        "docker-vs-k3s-edge-deployment": lambda c: m_containers(c, 3, 1),
        "can-bus-reverse-engineering-node-red": lambda c: m_frame(c),
        "siemens-s7-opcua-node-red": lambda c: m_secure_link(c, blocks=4, sink="chart"),
        "cicd-node-red-flows": lambda c: m_chain(c, 4, 2, feedback=True),
        "from-process-engineer-to-iiot-developer": lambda c: m_bridge(c),
        "lessons-learned-publishing-npm-packages": lambda c: m_packages(c, 5, 2),
        "kafka-shop-floor-event-streaming": lambda c: m_lanes(c, 5, 13, 2),
        "allen-bradley-ethernet-ip-node-red": lambda c: m_rack(c, slots=8, accent_slot=0),
        "modbus-node-red": lambda c: m_bus(c, drops=5, accent_index=2),
        "securing-ot-networks-opcua-purdue": lambda c: m_layers(c, 5, 2),
    },
}


# --------------------------------------------------------------- social card
# assets/img/og-base.png is the canvas layouts/partials/og-image.html writes
# page titles onto; og-default.png is the standalone card for the home page
# and anything with no title of its own. Both were a teal-to-indigo gradient
# with a mint rule — the site's old identity, and the one thing every share
# on LinkedIn or Slack still showed after the redesign. Drawn here so they
# come from the same palette as everything else.

OG_W, OG_H = 1200, 630


def og_canvas(with_brand=True):
    """Paper, an oxide rule where the mint bar used to be, and a schematic in
    the right third — the same vocabulary as the covers, held back to a rule
    weight so an overlaid title always wins."""
    c = Canvas("og")
    c.parts = []

    # The mark: a short accent rule, top left, where the mint bar sat.
    c.add(f'<rect x="80" y="86" width="88" height="5" rx="2" fill="{ACCENT}"/>')

    # A bus with drops, echoing the covers, kept faint. It sits in the top
    # right band and stops above y=170: og-image.html writes up to four title
    # lines of 64px starting at y=185, and at 24 characters a line reaches
    # roughly x=920, so anywhere lower on this side would be written over.
    bx, by = 706, 58
    c.line(bx, by, bx + 414, by, RULE_STRONG, LINE)
    for x in (bx, bx + 414):
        c.line(x, by - 11, x, by + 11, RULE_STRONG, LINE)
    for i in range(4):
        dx = bx + 72 + i * 90
        hit = i == 1
        c.line(dx, by, dx, by + 26, ACCENT if hit else RULE_STRONG,
               LINE if hit else HAIR)
        c.rect(dx - 32, by + 26, 64, 62,
               ACCENT if hit else RULE_STRONG, LINE if hit else HAIR)
        c.line(dx - 32, by + 42, dx + 32, by + 42, RULE_STRONG, HAIR)

    body = "\n  ".join(c.parts)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{OG_W}" height="{OG_H}" '
           f'viewBox="0 0 {OG_W} {OG_H}">\n'
           f'  <rect width="{OG_W}" height="{OG_H}" fill="{PAPER}"/>\n'
           f'  {body}\n</svg>\n')
    png = cairosvg.svg2png(bytestring=svg.encode(),
                           output_width=OG_W, output_height=OG_H)
    return Image.open(io.BytesIO(png)).convert("RGB")


def write_og():
    from PIL import ImageDraw, ImageFont
    font_path = os.path.join(REPO_ROOT, "assets", "fonts", "og-title.ttf")

    def brand(img, size=30, fill=INK_SOFT):
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype(font_path, size)
        t = "blanpa.github.io"
        w = d.textbbox((0, 0), t, font=f)[2]
        d.text((OG_W - 80 - w, OG_H - 84), t, font=f, fill=fill)

    # The canvas the title is written onto at build time.
    base = og_canvas()
    brand(base)
    base.save(os.path.join(REPO_ROOT, "assets", "img", "og-base.png"))

    # The standalone card.
    card = og_canvas()
    d = ImageDraw.Draw(card)
    d.text((80, 128), "IIoT Software Developer",
           font=ImageFont.truetype(font_path, 30), fill=ACCENT)
    d.text((80, 186), "blanpa", font=ImageFont.truetype(font_path, 92), fill=INK)
    d.text((80, 320), "Node-RED  ·  OPC-UA  ·  NATS  ·  Edge Computing",
           font=ImageFont.truetype(font_path, 28), fill=INK_SOFT)
    brand(card)
    card.save(os.path.join(REPO_ROOT, "assets", "img", "og-default.png"))
    print("  assets/img/og-base.png, assets/img/og-default.png")


def draw(section, slug):
    c = Canvas(f"{section}/{slug}")
    COVERS[section][slug](c)
    return c.render()


def write(section, slug, keep_svg=False):
    svg = draw(section, slug)
    folder = os.path.join(REPO_ROOT, "content", section, slug)
    if not os.path.isdir(folder):
        print(f"  SKIP {section}/{slug}: no such folder")
        return False
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H)
    out = os.path.join(folder, "featured.webp")
    Image.open(io.BytesIO(png)).convert("RGB").save(
        out, "WEBP", quality=88, method=6)
    if keep_svg:
        with open(os.path.join(folder, "cover.svg"), "w") as fh:
            fh.write(svg)
    print(f"  {section}/{slug}: {os.path.getsize(out) // 1024} KB")
    return True


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    keep_svg = "--svg" in sys.argv[1:]

    section = argv[0] if argv else "all"
    only = argv[1] if len(argv) > 1 else None
    if section in ("og", "all"):
        print("\n=== social card ===")
        write_og()
        if section == "og":
            return 0
    if section == "all":
        sections = list(COVERS)
    elif section in COVERS:
        sections = [section]
    else:
        sections, only = list(COVERS), section

    n = 0
    for sec in sections:
        slugs = sorted(s for s in COVERS[sec] if not only or only in s)
        if not slugs:
            continue
        print(f"\n=== {sec} ({len(slugs)}) ===")
        for slug in slugs:
            n += write(sec, slug, keep_svg)
    print(f"\n{n} covers drawn")
    return 0


if __name__ == "__main__":
    sys.exit(main())

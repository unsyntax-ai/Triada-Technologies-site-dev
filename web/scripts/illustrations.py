"""Topic illustrations for Insights posts.

The AI only chooses which illustration fits an article and a few settings for it
(for example how high each bar is, or where a needle points). This file does all
the drawing, so every picture is clean, on brand and safe, and no two topics look alike.

Each illustration is one idea in flat shapes: navy and teal carry the drawing,
white gives contrast, and a single small orange dot is the highlight. They sit on
a soft navy, teal or orange tint with a faint dot pattern, in the golden-ratio
shape of the cards (485 x 300).

Use:  draw("compass", {"heading": 40}, tint="mist")  ->  complete SVG text
"""
import math

W, H = 485, 300
INK, NAVY, TEAL, ORANGE, WHITE = "#0F172A", "#1E3A8A", "#14B8A6", "#FF6A00", "#FFFFFF"
SOFT = "#C9D3EE"      # passed / inactive marks
FAINT = "#E4E9F5"     # quiet lines on white
# background tint and the slightly darker dots on it
TINTS = {"mist": ("#EEF2FB", "#D6DEF2"), "teal": ("#E6F6F3", "#C9ECE6"), "sand": ("#FFF1E6", "#FBDCC6")}


# ---------- settings helpers: anything odd falls back to a safe default ----------
def _num(p, key, lo, hi, default):
    try:
        v = float(p.get(key, default))
    except (TypeError, ValueError):
        return default
    if math.isnan(v):
        return default
    return min(hi, max(lo, v))


def _choice(p, key, options, default):
    v = p.get(key, default)
    return v if v in options else default


def _f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------- the illustrations ----------
def compass(p, t):
    """Navigating change, direction, strategy."""
    heading = _num(p, "heading", 0, 359, 38)
    return f'''
<path d="M330 236C372 214 398 176 392 124" fill="none" stroke="{NAVY}" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 12" opacity=".55"/>
<circle cx="392" cy="118" r="7" fill="{NAVY}"/>
<circle cx="249" cy="158" r="92" fill="{t[1]}"/>
<circle cx="242" cy="150" r="92" fill="{WHITE}"/>
<circle cx="242" cy="150" r="74" fill="none" stroke="{FAINT}" stroke-width="2"/>
<rect x="239" y="66" width="6" height="14" rx="3" fill="{NAVY}"/>
<rect x="239" y="220" width="6" height="14" rx="3" fill="{SOFT}"/>
<rect x="312" y="147" width="14" height="6" rx="3" fill="{SOFT}"/>
<rect x="158" y="147" width="14" height="6" rx="3" fill="{SOFT}"/>
<g transform="rotate({_f(heading)} 242 150)">
<polygon points="242,92 256,150 228,150" fill="{NAVY}"/>
<polygon points="228,150 256,150 242,208" fill="{TEAL}"/>
</g>
<circle cx="242" cy="150" r="10" fill="{WHITE}"/><circle cx="242" cy="150" r="4.5" fill="{ORANGE}"/>'''


def bars(p, t):
    """Demand, growth or decline, hiring trends over time."""
    vals = p.get("values")
    if not isinstance(vals, list):
        vals = []
    clean = []
    for v in vals[:6]:
        try:
            clean.append(min(100.0, max(8.0, float(v))))
        except (TypeError, ValueError):
            pass
    if len(clean) < 4:
        clean = [38, 57, 46, 76, 100]
    n, bw, span, base = len(clean), 36, 250, 228
    gap = (span - n * bw) / (n - 1)
    x0 = (W - span) / 2
    top = max(clean)
    peak = clean.index(top)
    out = [f'<rect x="{_f(x0 - 16)}" y="{base}" width="{_f(span + 32)}" height="4" rx="2" fill="{t[1]}"/>']
    points = []
    for i, v in enumerate(clean):
        h = 168 * v / 100
        x = x0 + i * (bw + gap)
        fill = TEAL if i == peak else (NAVY if i == n - 1 else WHITE)
        out.append(f'<rect x="{_f(x)}" y="{_f(base - h)}" width="{bw}" height="{_f(h)}" rx="8" fill="{fill}"/>')
        points.append((x + bw / 2, base - h - 20))
    out.append('<polyline points="' + " ".join(f"{_f(a)},{_f(b)}" for a, b in points) +
               f'" fill="none" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, (a, b) in enumerate(points):
        if i == peak:
            out.append(f'<circle cx="{_f(a)}" cy="{_f(b)}" r="8" fill="{ORANGE}"/>')
        else:
            out.append(f'<circle cx="{_f(a)}" cy="{_f(b)}" r="5" fill="{WHITE}" stroke="{NAVY}" stroke-width="3"/>')
    return "\n".join(out)


def gauge(p, t):
    """Pay levels, market temperature, how strong something is."""
    level = _num(p, "level", 0, 100, 78)
    cx, cy, r = 242, 210, 110

    def pt(deg, rad=r):
        a = math.radians(deg)
        return cx - rad * math.cos(a), cy - rad * math.sin(a)

    segs = [(0, 58, WHITE), (62, 118, TEAL), (122, 180, NAVY)]
    out = []
    for a, b, c in segs:
        (x1, y1), (x2, y2) = pt(a), pt(b)
        out.append(f'<path d="M{_f(x1)} {_f(y1)}A{r} {r} 0 0 1 {_f(x2)} {_f(y2)}" fill="none" stroke="{c}" stroke-width="26"/>')
    out.append(f'<rect x="120" y="226" width="245" height="4" rx="2" fill="{t[1]}"/>')
    deg = level * 1.8
    tx, ty = pt(deg, 84)
    dx, dy = (tx - cx) / 84, (ty - cy) / 84
    nx, ny = -dy * 6, dx * 6
    out.append(f'<polygon points="{_f(cx + nx)},{_f(cy + ny)} {_f(cx - nx)},{_f(cy - ny)} {_f(tx)},{_f(ty)}" fill="{INK}"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="{INK}"/><circle cx="{cx}" cy="{cy}" r="5" fill="{ORANGE}"/>')
    return "\n".join(out)


def balance(p, t):
    """Choices and trade-offs, such as contract versus permanent hiring."""
    heavier = _choice(p, "heavier", ("left", "right", "even"), "left")
    ang = {"left": -8, "right": 8, "even": 0}[heavier]
    a = math.radians(ang)
    lx, ly = 242 - 106 * math.cos(a), 88 - 106 * math.sin(a)
    rx, ry = 242 + 106 * math.cos(a), 88 + 106 * math.sin(a)
    lp, rp = ly + 49, ry + 49
    return f'''
<rect x="196" y="226" width="92" height="12" rx="6" fill="{NAVY}"/>
<rect x="238" y="88" width="8" height="140" rx="4" fill="{NAVY}"/>
<g stroke="#94A3C4" stroke-width="2">
<line x1="{_f(lx)}" y1="{_f(ly)}" x2="{_f(lx - 27)}" y2="{_f(lp)}"/><line x1="{_f(lx)}" y1="{_f(ly)}" x2="{_f(lx + 27)}" y2="{_f(lp)}"/>
<line x1="{_f(rx)}" y1="{_f(ry)}" x2="{_f(rx - 27)}" y2="{_f(rp)}"/><line x1="{_f(rx)}" y1="{_f(ry)}" x2="{_f(rx + 27)}" y2="{_f(rp)}"/>
</g>
<rect x="132" y="84" width="220" height="8" rx="4" fill="{NAVY}" transform="rotate({ang} 242 88)"/>
<circle cx="242" cy="88" r="10" fill="{NAVY}"/><circle cx="242" cy="88" r="4" fill="{ORANGE}"/>
<rect x="{_f(lx - 17)}" y="{_f(lp - 34)}" width="34" height="34" rx="7" fill="{TEAL}"/>
<path d="M{_f(lx - 33)} {_f(lp)}H{_f(lx + 33)}Q{_f(lx)} {_f(lp + 38)} {_f(lx - 33)} {_f(lp)}Z" fill="{WHITE}"/>
<circle cx="{_f(rx)}" cy="{_f(rp - 16)}" r="16" fill="{NAVY}"/>
<path d="M{_f(rx - 33)} {_f(rp)}H{_f(rx + 33)}Q{_f(rx)} {_f(rp + 38)} {_f(rx - 33)} {_f(rp)}Z" fill="{WHITE}"/>'''


def bridge(p, t):
    """A skills gap, upskilling, closing a distance."""
    return f'''
<circle cx="384" cy="78" r="30" fill="{WHITE}" opacity=".85"/>
<rect x="64" y="192" width="118" height="130" rx="18" fill="{NAVY}"/>
<rect x="303" y="192" width="118" height="130" rx="18" fill="{TEAL}"/>
<rect x="172" y="132" width="7" height="62" rx="3.5" fill="{INK}"/>
<rect x="306" y="132" width="7" height="62" rx="3.5" fill="{INK}"/>
<path d="M175 136Q242 186 309 136" fill="none" stroke="{INK}" stroke-width="2.5" opacity=".35"/>
<rect x="183" y="180" width="26" height="13" rx="4" fill="{WHITE}"/>
<rect x="213" y="182" width="26" height="13" rx="4" fill="{WHITE}"/>
<rect x="273" y="180" width="26" height="13" rx="4" fill="{WHITE}"/>
<path d="M256 150V172" stroke="{ORANGE}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="1 7"/>
<rect x="243" y="122" width="26" height="13" rx="4" fill="{ORANGE}" transform="rotate(-14 256 128)"/>'''


def puzzle(p, t):
    """Fit and matching between people, roles and teams."""
    shadow = "#F6CDB0" if t[0] == TINTS["sand"][0] else t[1]
    return f'''
<rect x="126" y="103" width="110" height="110" rx="14" fill="{shadow}"/>
<rect x="120" y="95" width="110" height="110" rx="14" fill="{NAVY}"/>
<circle cx="230" cy="150" r="20" fill="{NAVY}"/>
<g transform="rotate(7 318 140)">
<rect x="269" y="93" width="110" height="110" rx="14" fill="{shadow}"/>
<rect x="263" y="85" width="110" height="110" rx="14" fill="{WHITE}"/>
<circle cx="263" cy="140" r="22" fill="{t[0]}"/>
</g>
<rect x="388" y="58" width="30" height="30" rx="7" fill="{TEAL}" transform="rotate(16 403 73)"/>
<circle cx="172" cy="150" r="7" fill="{ORANGE}"/>'''


def calendar(p, t):
    """Time to hire, deadlines, timing and speed."""
    day = int(_num(p, "day", 0, 19, 7))
    out = [f'''
<rect x="142" y="84" width="180" height="160" rx="16" fill="{t[1]}"/>
<rect x="136" y="76" width="180" height="160" rx="16" fill="{WHITE}"/>
<rect x="136" y="76" width="180" height="38" rx="16" fill="{NAVY}"/><rect x="136" y="98" width="180" height="16" fill="{NAVY}"/>
<rect x="166" y="64" width="8" height="24" rx="4" fill="{INK}"/><rect x="278" y="64" width="8" height="24" rx="4" fill="{INK}"/>''']
    for i in range(20):
        x, y = 162 + (i % 5) * 32, 134 + (i // 5) * 26
        if i == day:
            out.append(f'<circle cx="{x}" cy="{y}" r="10" fill="{TEAL}"/>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{SOFT if i < day else "#E8ECF6"}"/>')
    out.append(f'''<circle cx="336" cy="206" r="48" fill="{TEAL}"/><circle cx="336" cy="206" r="38" fill="{WHITE}"/>
<line x1="336" y1="206" x2="336" y2="180" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
<line x1="336" y1="206" x2="354" y2="214" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
<circle cx="336" cy="206" r="4.5" fill="{ORANGE}"/>''')
    return "\n".join(out)


def network(p, t):
    """Reach, remote and hybrid work, connections across the country."""
    count = int(_num(p, "nodes", 4, 7, 7))
    spots = [(120, 92, 11, WHITE), (138, 214, 13, TEAL), (330, 82, 12, WHITE), (372, 176, 10, WHITE),
             (300, 232, 8, NAVY), (96, 160, 7, NAVY), (392, 110, 7, ORANGE)]
    spots = spots[:count - 1] + [spots[-1]]
    links = [(242, 150, x, y) for x, y, _, _ in spots[:5]]
    if count >= 6:
        links.append((120, 92, 96, 160))
    links.append((spots[2][0], spots[2][1], 392, 110) if count >= 3 else (242, 150, 392, 110))
    line = f'<g stroke="{t[1] if t[0] != TINTS["teal"][0] else "#9ADBD1"}" stroke-width="3" stroke-linecap="round">'
    line += "".join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}"/>' for a, b, c, d in links) + "</g>"
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>' for x, y, r, c in spots)
    return (line + f'<circle cx="242" cy="150" r="36" fill="none" stroke="{NAVY}" stroke-width="2" opacity=".18"/>'
            f'<circle cx="242" cy="150" r="22" fill="{NAVY}"/>' + dots + f'<circle cx="242" cy="150" r="6" fill="{WHITE}"/>')


def ladder(p, t):
    """Career growth, promotion, moving up a level."""
    step = int(_num(p, "step", 1, 5, 3))
    out = [f'<g transform="rotate(8 242 156)">',
           f'<rect x="196" y="46" width="10" height="222" rx="5" fill="{NAVY}"/>',
           f'<rect x="278" y="46" width="10" height="222" rx="5" fill="{NAVY}"/>']
    for k in range(1, 6):
        y = 240 - (k - 1) * 42
        out.append(f'<rect x="206" y="{y}" width="72" height="8" rx="4" fill="{TEAL if k == step else SOFT}"/>')
    y = 240 - (step - 1) * 42
    out.append(f'<circle cx="242" cy="{y - 14}" r="10" fill="{ORANGE}"/>')
    out.append(f'<rect x="281" y="18" width="4" height="30" rx="2" fill="{INK}"/><polygon points="285,18 314,26 285,34" fill="{TEAL}"/>')
    out.append("</g>")
    out.append(f'<path d="M118 238C128 180 150 120 176 86" fill="none" stroke="{NAVY}" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 12" opacity=".5"/>')
    return "\n".join(out)


def search(p, t):
    """Screening, finding the right candidate, talent search."""
    pick = int(_num(p, "pick", 0, 5, 4))
    out = []
    for i in range(6):
        x, y = 120 + (i % 3) * 86, 66 + (i // 3) * 100
        on = i == pick
        out.append(f'<rect x="{x}" y="{y}" width="70" height="84" rx="12" fill="{WHITE}"/>')
        out.append(f'<circle cx="{x + 35}" cy="{y + 30}" r="13" fill="{TEAL if on else FAINT}"/>')
        out.append(f'<rect x="{x + 16}" y="{y + 52}" width="38" height="6" rx="3" fill="{NAVY if on else FAINT}"/>')
        out.append(f'<rect x="{x + 22}" y="{y + 64}" width="26" height="6" rx="3" fill="{FAINT}"/>')
    x, y = 120 + (pick % 3) * 86 + 35, 66 + (pick // 3) * 100 + 42
    out.append(f'<circle cx="{x}" cy="{y}" r="50" fill="{WHITE}" fill-opacity=".22" stroke="{NAVY}" stroke-width="9"/>')
    out.append(f'<line x1="{_f(x + 37)}" y1="{_f(y + 37)}" x2="{_f(x + 66)}" y2="{_f(y + 66)}" stroke="{NAVY}" stroke-width="14" stroke-linecap="round"/>')
    out.append(f'<circle cx="{x + 30}" cy="{y - 40}" r="8" fill="{ORANGE}"/>')
    return "\n".join(out)


def blocks(p, t):
    """Skill stacks, layers of a tech stack, building capability."""
    count = int(_num(p, "layers", 3, 5, 4))
    out, y = [], 236
    for i in range(count):
        w = 220 - i * 34
        fill = TEAL if i == count - 1 else (NAVY if i % 2 == 0 else WHITE)
        out.append(f'<rect x="{_f(242 - w / 2 + 6)}" y="{y - 30 + 6}" width="{w}" height="30" rx="9" fill="{t[1]}"/>')
        out.append(f'<rect x="{_f(242 - w / 2)}" y="{y - 30}" width="{w}" height="30" rx="9" fill="{fill}"/>')
        y -= 38
    out.append(f'<path d="M242 {y - 14}V{y + 4}" stroke="{ORANGE}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="1 7"/>')
    out.append(f'<rect x="222" y="{y - 52}" width="40" height="30" rx="9" fill="{ORANGE}" transform="rotate(-10 242 {y - 37})"/>')
    return "\n".join(out)


def paths(p, t):
    """Career paths, decisions, two directions to choose from."""
    chosen = _choice(p, "chosen", ("left", "right"), "right")
    left = "M242 300V214C242 160 160 156 150 74"
    right = "M242 300V214C242 160 324 156 334 74"
    out = [f'<path d="{left}" fill="none" stroke="{WHITE}" stroke-width="30" stroke-linecap="round"/>',
           f'<path d="{right}" fill="none" stroke="{WHITE}" stroke-width="30" stroke-linecap="round"/>',
           f'<path d="{left}" fill="none" stroke="{SOFT}" stroke-width="3" stroke-linecap="round" stroke-dasharray="10 12"/>',
           f'<path d="{right}" fill="none" stroke="{SOFT}" stroke-width="3" stroke-linecap="round" stroke-dasharray="10 12"/>']
    win, lose = ((150, 74), (334, 74)) if chosen == "left" else ((334, 74), (150, 74))
    out.append(f'<circle cx="{lose[0]}" cy="{lose[1]}" r="12" fill="{SOFT}"/>')
    out.append(f'<circle cx="{win[0]}" cy="{win[1]}" r="20" fill="{NAVY}"/><circle cx="{win[0]}" cy="{win[1]}" r="7" fill="{ORANGE}"/>')
    out.append(f'<circle cx="242" cy="214" r="9" fill="{TEAL}"/>')
    return "\n".join(out)


# name -> (drawing, what it means, settings the AI may give, default tint)
MOTIFS = {
    "compass":  (compass,  "navigating change, direction, strategy", '"heading": 0-359 (needle angle)', "mist"),
    "bars":     (bars,     "demand, growth or decline, trends over time", '"values": 4-6 numbers 0-100, oldest first', "teal"),
    "gauge":    (gauge,    "pay levels, market temperature, intensity", '"level": 0-100 (needle position)', "sand"),
    "balance":  (balance,  "choices and trade-offs, such as contract versus permanent", '"heavier": "left" | "right" | "even"', "mist"),
    "bridge":   (bridge,   "a skills gap, upskilling, closing a distance", "none", "teal"),
    "puzzle":   (puzzle,   "fit and matching between people, roles and teams", "none", "sand"),
    "calendar": (calendar, "time to hire, deadlines, timing and speed", '"day": 0-19 (highlighted day)', "mist"),
    "network":  (network,  "reach, remote and hybrid work, nationwide connections", '"nodes": 4-7', "teal"),
    "ladder":   (ladder,   "career growth, promotion, levelling up", '"step": 1-5 (highlighted rung)', "sand"),
    "search":   (search,   "screening, finding the right candidate", '"pick": 0-5 (which profile is found)', "mist"),
    "blocks":   (blocks,   "skill stacks, layers of technology, building capability", '"layers": 3-5', "teal"),
    "paths":    (paths,    "career paths and decisions between two directions", '"chosen": "left" | "right"', "sand"),
}

LABELS = {"compass": "A compass", "bars": "A bar chart with a trend line", "gauge": "A gauge",
          "balance": "A balance scale", "bridge": "A bridge being completed across a gap",
          "puzzle": "Two puzzle pieces about to fit", "calendar": "A calendar and a clock",
          "network": "A network of connected points", "ladder": "A ladder with one rung highlighted",
          "search": "A magnifying glass over candidate profiles", "blocks": "A stack of building blocks",
          "paths": "A road splitting into two paths"}

# words that point to each illustration, used when the AI's choice is missing or invalid
KEYWORDS = {
    "gauge": ["pay", "salary", "salaries", "wage", "compensation", "temperature"],
    "balance": ["contract", "permanent", "versus", "vs", "trade-off", "tradeoff"],
    "bridge": ["gap", "upskill", "reskill", "training", "shortage"],
    "puzzle": ["fit", "match", "culture", "team"],
    "calendar": ["time", "speed", "fast", "deadline", "timeline", "quarter"],
    "network": ["remote", "hybrid", "nationwide", "location", "region", "states"],
    "ladder": ["career", "promotion", "growth", "senior", "level"],
    "search": ["screen", "screening", "candidate", "search", "find", "interview"],
    "blocks": ["stack", "skills", "cloud", "ai", "layer", "platform"],
    "paths": ["path", "choice", "decision", "pivot", "switch"],
    "compass": ["navigating", "navigate", "shift", "change", "direction"],
    "bars": ["trend", "demand", "rise", "decline", "growth", "postings"],
}


def guess(text, avoid=()):
    """Pick an illustration from the words of an article, skipping recently used ones when possible."""
    words = set(w.strip(".,:;!?()'\"").lower() for w in text.split())
    scores = {m: sum(1 for k in keys if k in words) for m, keys in KEYWORDS.items()}
    ranked = sorted(MOTIFS, key=lambda m: (-scores.get(m, 0), m in avoid))
    fresh = [m for m in ranked if m not in avoid]
    return (fresh or ranked)[0]


def draw(motif, params=None, tint=None):
    """Return the finished SVG for one illustration. Unknown names fall back to the bar chart."""
    if motif not in MOTIFS:
        motif = "bars"
    fn, _, _, default_tint = MOTIFS[motif]
    t = TINTS.get(tint) or TINTS[default_tint]
    params = params if isinstance(params, dict) else {}
    body = fn(params, t)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{LABELS[motif]}">'
            f'<defs><pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">'
            f'<circle cx="2" cy="2" r="1.5" fill="{t[1]}"/></pattern></defs>'
            f'<rect width="{W}" height="{H}" fill="{t[0]}"/><rect width="{W}" height="{H}" fill="url(#dots)"/>'
            f'{body}</svg>')


def menu():
    """The list of illustrations as text for the AI prompt."""
    return "\n".join(f'- "{name}": {meaning}. Settings: {settings}.'
                     for name, (_, meaning, settings, _) in MOTIFS.items())


if __name__ == "__main__":
    # python scripts/illustrations.py <file.html>  ->  writes a preview page of every illustration
    import sys
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/illustrations.py <preview.html>")
    cards = "".join(f'<figure style="margin:0"><div style="border-radius:16px;overflow:hidden">{draw(m)}</div>'
                    f'<figcaption style="font:14px sans-serif;margin-top:6px">{m}</figcaption></figure>' for m in MOTIFS)
    page = ('<!doctype html><meta charset="utf-8"><title>Illustrations</title><body style="margin:24px;background:#FAFAFA">'
            '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:21px">' + cards + "</div>")
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", sys.argv[1])
